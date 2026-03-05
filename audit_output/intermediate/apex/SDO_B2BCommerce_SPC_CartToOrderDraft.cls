public class SDO_B2BCommerce_SPC_CartToOrderDraft {

    public class Request {
        
        @InvocableVariable(required=true)
        public ID checkoutSessionId;
        
        @InvocableVariable(required=true)
        public ID cartId;

        @InvocableVariable(required=false)
        public ID pricebookId;
    }
    
    /**
     * @description Maps a cart to an order. Activates it, and closes the cart. Returns the resulting order summary id.
     * @param request The checkout session and cart id.
     * @return The OrderId that resulted from this class.
     */
    @InvocableMethod(label='B2B Map Cart to Order Draft' description='Maps the cart and related data to an order' category='B2B Commerce')
    public static List<ID> cartToOrder(List<Request> request) {
        
        // screen flows do not run in bulk
        Id cartId = request[0].cartId;
        Id checkoutSessionId = request[0].checkoutSessionId;
        
        // load the primary delivery group (only one supported at this time)
        Id cartDeliveryGroupId = [SELECT Id FROM CartDeliveryGroup WHERE CartId = :cartId][0].Id;

        Order order = mapAndInsertCartToOrder(request[0]);

        // 2020-12-15 msobczak@salesforce.com  -  updated for test coverage
        if(checkoutSessionId != null) {
            updateCheckoutSession(checkoutSessionId, order.Id);
        }
        
        Id orderDeliveryGroupId = mapAndInsertCartDeliveryGroupToOrderDeliveryGroup(cartDeliveryGroupId, order.Id);
        mapAndInsertCartItems(cartDeliveryGroupId, order, orderDeliveryGroupId, request[0]);
        
        //2021-10-05 dspagnuolo: override order amount to consider cart lever promotions
        applyCartLevelPromotionsToOrder(order, cartId);
                
        List<ID> orderIds = new List<ID>();
        orderIds.add(order.Id);
        return orderIds;
    }
    
    /**
     * @description Satisfy the preconditions required to use the following call to Activate the Order
     */
    private static void updateCheckoutSession(Id checkoutSessionId, Id orderId) {
        try {
            CartCheckoutSession checkoutSession = [SELECT OrderId, NextState FROM CartCheckoutSession WHERE Id = :checkoutSessionId LIMIT 1];
            checkoutSession.OrderId = orderId;
            checkoutSession.NextState = 'Complete';
            update checkoutSession;
        } catch (Exception e) {
            System.debug('An error occurred updating checkout session with the draft order Id');
        }
    }
    
    /**
     * @description Maps the cart entity to an order entity and returns the id of the order entity that was created.
     * @param cartId The cart id to map to an order.
     * @return The id of the order that was created.
     */
    private static Order mapAndInsertCartToOrder(Request request) {
        // Get the cart data needed to populate the order
        List<WebCart> carts = [SELECT Id,
                               AccountId,
                               OwnerId,
                               WebStoreId,
                               PoNumber,
                               BillingStreet,
                               BillingCity,
                               BillingState,
                               BillingPostalCode,
                               BillingCountry,
                               BillingLatitude,
                               BillingLongitude
                               //,CurrencyIsoCode
                               FROM WebCart WHERE Id = :request.cartId];
        WebCart cart = carts[0];
        
        // Create the order
        Date now = Date.today();    
        Order order = new Order(
            AccountId = cart.AccountId,
            OwnerId = cart.OwnerId,
            SalesStoreId = cart.WebStoreId,
            PoNumber = cart.PoNumber,
            BillingStreet = cart.BillingStreet,
            BillingCity = cart.BillingCity,
            BillingState = cart.BillingState,
            BillingPostalCode = cart.BillingPostalCode,
            BillingCountry = cart.BillingCountry,
            BillingLatitude = cart.BillingLatitude,
            BillingLongitude = cart.BillingLongitude,
            //,CurrencyIsoCode = cart.CurrencyIsoCode,
            EffectiveDate = now,
            // FFEIX[03/17/23] : set date & time on Ordered Date
            OrderedDate = Datetime.now(),
            Status = 'Draft'
            ,Pricebook2Id = request.pricebookId
        );
        
        insert(order);
        return order;
    }
    
    /**
     * @description Maps the cart delivery group entity to an order delivery group entity and returns the id of the
     *              order delivery group entity that was created.
     * @param cartDeliveryGroupId The cartDeliveryGroup id to map.
     * @param orderId The orderDeliveryGroup is linked to the original order.
     * @return The id of the order delivery group that was created.
     */
    private static Id mapAndInsertCartDeliveryGroupToOrderDeliveryGroup(Id cartDeliveryGroupId, Id orderId) {
        // Get the cart delivery group data needed to populate the order delivery group
        List<CartDeliveryGroup> cartDeliveryGroups = [SELECT
                                                      DesiredDeliveryDate,
                                                      DeliverToName,
                                                      ShippingInstructions,
                                                      DeliverToStreet,
                                                      DeliverToCity,
                                                      DeliverToState,
                                                      DeliverToPostalCode,
                                                      DeliverToCountry,
                                                      DeliverToLatitude,
                                                      DeliverToLongitude,
                                                      DeliveryMethodId
                                                      FROM CartDeliveryGroup WHERE Id = :cartDeliveryGroupId];
        CartDeliveryGroup cartDeliveryGroup = cartDeliveryGroups[0];
        
        // Create the order delivery group
        Date desiredDeliveryDate = toDate(cartDeliveryGroup.DesiredDeliveryDate);
        OrderDeliveryGroup orderDeliveryGroup = new OrderDeliveryGroup(
            DesiredDeliveryDate = desiredDeliveryDate,
            DeliverToName = cartDeliveryGroup.DeliverToName,
            DeliveryInstructions = cartDeliveryGroup.ShippingInstructions,
            DeliverToStreet = cartDeliveryGroup.DeliverToStreet,
            DeliverToCity = cartDeliveryGroup.DeliverToCity,
            DeliverToState = cartDeliveryGroup.DeliverToState,
            DeliverToPostalCode = cartDeliveryGroup.DeliverToPostalCode,
            DeliverToCountry = cartDeliveryGroup.DeliverToCountry,
            DeliverToLatitude = cartDeliveryGroup.DeliverToLatitude,
            DeliverToLongitude = cartDeliveryGroup.DeliverToLongitude,
            OrderDeliveryMethodId = cartDeliveryGroup.DeliveryMethodId,
            OrderId = orderId
        );

        insert(orderDeliveryGroup);
        return orderDeliveryGroup.Id;
    }
    
    /**
     * @description Maps the cart items to a set of order items. This also creates order item adjustments.
     *              Tax adjustments could probably also be done here, but are not part of the example.
     * @param cartDeliveryGroupId the cartDeliveryGroup id for this set of cart items.
     * @param orderId The items are linked to the original order.
     * @param orderDeliveryGroupId The items are linked to the order delivery group.
     */
    private static void mapAndInsertCartItems(Id cartDeliveryGroupId, Order order, Id orderDeliveryGroupId, Request request) {
        // Get the cart items needed to populate the order items and adjustments
        List<CartItem> cartItems = [SELECT
                                    AdjustmentAmount,
                                    Product2Id,
                                    Type,
                                    Quantity,
                                    ListPrice,
                                    SalesPrice,
                                    TotalLineAmount,
                                    
                                    //2021-10-05 dspagnuolo: this contains the price net promotions
                                    TotalAmount, 
                                    TotalLineTaxAmount

                                    // FFEIX[03/17/23] : Store Product Name in OrderItem Description
                                    , Name

                                    FROM CartItem WHERE CartDeliveryGroupId = :cartDeliveryGroupId];

        Map<Id, Id> pbeProductMap = new Map<Id, Id>();

        // 2020-12-17 msobczak: only do this logic for test coverage purposes

        if(request.pricebookId != null) {
            List<PricebookEntry> pbeList = [Select Id, Product2Id from PricebookEntry where Pricebook2Id = :request.pricebookId];

            for(PricebookEntry pbe : pbeList) {
                pbeProductMap.put(pbe.Product2Id, pbe.Id);
            }
        }
        
        List<OrderItem> orderItems = new List<OrderItem>();
        // For each item, map it to an order, then add adjustments
        for (CartItem cartItem : cartItems) {
            //orderItems.add(mapCartItemToOrderItem(cartItem, orderId, orderDeliveryGroupId));
            OrderItem oi = mapCartItemToOrderItem(cartItem, order, orderDeliveryGroupId);

            if(pbeProductMap.containsKey(cartItem.Product2Id)) {
                System.debug('PBE applied to product');
                oi.PricebookEntryId = pbeProductMap.get(cartItem.Product2Id);
            }

            orderItems.add(oi);

        }
        
        // If there are no items to insert, we can't do anything
        if (orderItems.size() == 0 || cartItems.size() != orderItems.size()) {
            return;
        }
        
        insert(orderItems);

        List<OrderItemAdjustmentLineItem> lineItemAdjustments = new List<OrderItemAdjustmentLineItem>();
        for (Integer index = 0; index < cartItems.size(); index++) {
            OrderItemAdjustmentLineItem lineItemAdjustment = mapOrderItemAdjustmentLineItemTo(cartItems.get(index), orderItems.get(index).Id);
            if (lineItemAdjustment != null) {
                lineItemAdjustments.add(lineItemAdjustment);
            }
        }
        if (lineItemAdjustments.size() > 0) {
            insert(lineItemAdjustments);
        }

        // 2020-11-30 msobczak: changes to apply tax

        List<OrderItemTaxLineItem> oitliList = new List<OrderItemTaxLineItem>();

        Map<String, CartTax> cartTaxItemMap = new Map<String, CartTax>();

        List<CartTax> cartTaxItemList = [Select Id, Name, Amount, CartItemId, TaxCalculationDate, TaxRate, TaxType from CartTax where CartId = :request.cartId];

        for(CartTax ct : cartTaxItemList) {
            cartTaxItemMap.put(ct.CartItemId, ct);
        }

        for (Integer index = 0; index < cartItems.size(); index++) {

            System.debug('index: ' + index);
            
            CartItem cartItem = cartItems.get(index);
            OrderItem orderItem = orderItems.get(index);

            System.debug('cartItem: ' + cartItem);
            System.debug('orderItem: ' + orderItem);

            // Create Order Product Tax Line Item
            OrderItemTaxLineItem oitli = new OrderItemTaxLineItem();
            CartTax cartTax = cartTaxItemMap.get(cartItem.Id);

            System.debug('cartTax: ' + cartTax);

            oitli.Name = cartTax.Name;
            oitli.Amount = cartTax.Amount;
            oitli.OrderItemId = orderItem.Id;
            oitli.Rate = cartTax.TaxRate;
            oitli.TaxEffectiveDate = cartTax.TaxCalculationDate;
            oitli.Type = 'Actual';

            oitliList.add(oitli);

        }

        insert(oitliList);

    }
    
    /**
     * @description Maps the cart item to an order item.
     * @param cartItem The cartItem to map to an order item.
     * @param orderId The item is linked to the original order.
     * @param orderDeliveryGroupId The item is linked to the order delivery group.
     * @return The order item to be inserted.
     */
    private static OrderItem mapCartItemToOrderItem(CartItem cartItem, Order order, Id orderDeliveryGroupId) {
        String orderItemType = getOrderItemType(cartItem.Type);
        Decimal unitPrice = getUnitPrice(cartItem);
        
        OrderItem orderItem = new OrderItem(
            Product2Id = cartItem.Product2Id,
            Type = orderItemType,
            Quantity = cartItem.Quantity,
            ListPrice = cartItem.ListPrice,  // 2020-12-15 was commented out
            UnitPrice = unitPrice,
            OrderId = order.Id,
            OrderDeliveryGroupId = orderDeliveryGroupId,
            TotalLineAmount = cartItem.TotalLineAmount

            // 2020-12-17 msobczak: added for test coverage purposes
            , ServiceDate = order.EffectiveDate
            , EndDate = order.EndDate

            // FFEIX[03/17/23] : Store Product Name in OrderItem Description
            , Description = cartItem.Name
        );

        if(cartItem.ListPrice == null) {
            orderItem.ListPrice = unitPrice;
        }
        else {
            orderItem.ListPrice = cartItem.ListPrice;
        }
        
        return orderItem;
    }
    


    /**
     * @description Maps the cart item to create an adjustment line item. If the item would normally cost
     *              $100, but costs $80, this is where that adjustment is recorded.
     * @param cartItem The cartItem to map to an order adjustment line item.
     * @param orderItemId The adjustment is mapped to an order item.
     * @return The order item adjustment to be inserted.
     */
    private static OrderItemAdjustmentLineItem mapOrderItemAdjustmentLineItemTo(CartItem cartItem, Id orderItemId) {
        Decimal adjustmentAmount = getAdjustmentAmount(cartItem);
        if (adjustmentAmount == null || adjustmentAmount == 0.0) {
            return null;
        }
        
        OrderItemAdjustmentLineItem orderItemAdjustmentLineItem = new OrderItemAdjustmentLineItem(
            Amount = adjustmentAmount,
            OrderItemId = orderItemId,
            Name = 'Price Adjustment'
        );
        
        return orderItemAdjustmentLineItem;
    }    
    
    /**
     * Creates the order adjustment groups at header level to map cart-level promos 
     * @author dspagnuolo
     * @param order the order that is being created
     * @param cartId the id of the generating cart
     */
    private static void applyCartLevelPromotionsToOrder(Order order, Id cartId) {
        //getting cart adjustments from cart
        List<WebCartAdjustmentGroup> cartPromos = [
            SELECT AdjustmentSource,
                AdjustmentTargetType,
                AdjustmentType,
                AdjustmentValue,
                CartId,
                Description,
                Name,
                TotalAmount,
                TotalAmountWithTax 
                FROM WebCartAdjustmentGroup WHERE CartId = :cartId];
        
        //in order to apply the discount, we distribute the cart level promo between the items
        List<OrderItemAdjustmentLineItem> distributedLineAdjustments = new List<OrderItemAdjustmentLineItem>();
        
        List<CartItem> cartItems = [SELECT ID, Product2Id   
                                    FROM CartItem WHERE CartId = :cartId AND Type = 'Product'];
        
        for (integer i=0; i<cartPromos.size(); i++) {
            WebCartAdjustmentGroup cartPromo = cartPromos.get(i);
            Decimal splittedPromo = (Decimal) cartPromo.TotalAmount / cartItems.size();
            Decimal splittedPromoWithTax = (Decimal) cartPromo.TotalAmountWithTax / cartItems.size();
            
            for (integer j=0; j<cartItems.size(); j++) {
                CartItem cartItem = cartItems.get(j);
                
                //getting the related order item
                OrderItem oi = [SELECT Id FROM OrderItem WHERE OrderId = :order.Id AND Product2Id = :cartItem.Product2Id][0];
                
                OrderItemAdjustmentLineItem lineAdjustment = new OrderItemAdjustmentLineItem();
                lineAdjustment.Amount = splittedPromo;
                lineAdjustment.Name = cartPromo.AdjustmentSource;
                lineAdjustment.OrderItemId = oi.Id;
                
                distributedLineAdjustments.add(lineAdjustment);
            }
        }
        
        insert distributedLineAdjustments;
    }

    /**
     * @description Gets the adjustment amount from the cart item. If none exists, returns zero.
     * @param cartItem Where to get the adjustment amount from.
     * @return The adjustment amount (0, if there is no adjustment).
     */
    private static Decimal getAdjustmentAmount(CartItem cartItem) {
        if (cartItem.AdjustmentAmount == null) {
            return 0;
        }
        
        //2021-10-05 dspagnuolo: modified to consider promotions
        if (cartItem.TotalAmount != cartItem.TotalLineAmount) {
        	//means that there is a promo applied
        	//we must get the adjustment amount before taxes
        	return (cartItem.TotalAmount - cartItem.TotalLineTaxAmount - cartItem.TotalLineAmount) + cartItem.AdjustmentAmount;
        }
        
        return cartItem.AdjustmentAmount;
    }
    
    /**
     * @description Gets the order item type from the sales item type. This maps the cart item type to the order item type.
     * @param salesItemType The cart item's type.
     * @return The order Item Type or null if the type doesn't map.
     */
    private static String getOrderItemType(String cartItemType) {
        if (cartItemType == 'Product') {
            return 'Order Product';
        }
        if (cartItemType == 'Charge') {
            return 'Delivery Charge';
        }
        
        return null;
    }

    /**
     * @description Gets the unit price from the cart item. This tries to use the sales price but will default to the list price
     *              if there is no sales price.
     * @param cartItem The item that has the prices.
     * @return The unit price.
     */
    private static Decimal getUnitPrice(CartItem cartItem) {
        if (cartItem.SalesPrice != null) {
            return cartItem.SalesPrice;
        }

        return cartItem.ListPrice;
    }
    
    /**
     * @description Converts a DateTime object to a Date object.
     * @param dt The datetime to convert.
     * @return The new Date.
     */
    private static Date toDate(DateTime dt) {
        if (dt != null) {
            return Date.newinstance(dt.year(), dt.month(), dt.day());
        }
        
        return null;
    }
}