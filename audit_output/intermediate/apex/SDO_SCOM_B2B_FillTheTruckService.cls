public with sharing class SDO_SCOM_B2B_FillTheTruckService {
    public static List<String> getProductIdsFromCartItems(List<ConnectApi.CartItemResult> cartItems) {
        List<String> productIds = new List<String>();
        for (ConnectApi.CartItemResult cartItem : cartItems) {
            productIds.add(cartItem.cartItem.productId);
        }
        return productIds;
    }

    public static List<Product2> getProdcutCubicSizes(List<String> productIds) {
        List<Product2> productsData = [SELECT Id, Sdo_Scom_B2B_Shipping_Cubic_Size__c FROM Product2 WHERE Id IN :productIds];
        return productsData;
    }

    @AuraEnabled
    public static Decimal getFilledCapacity(String webstoreId, String effectiveAccountId){
        try {
            List<ConnectApi.CartItemResult> cartItems = new List<ConnectApi.CartItemResult>();
            String cartId = 'current';
            String pageToken = null;
            Integer pageSize = 100;
            // Load all cart items
            do {
                ConnectApi.CartItemCollection cartItemCollection = ConnectApi.CommerceCart.getCartItems(webstoreId, effectiveAccountId, cartId, pageToken, pageSize);
                cartItems.addAll(cartItemCollection.cartItems);
                pageToken = cartItemCollection.nextPageToken;
            } while (pageToken != null);
            // Extract Product Ids from Cart Items
            List<String> productIds = getProductIdsFromCartItems(cartItems);
            // Get Products Cubic Size
            List<Product2> productsData = getProdcutCubicSizes(productIds);
            Map<Id, Product2> mappedProductData = new Map<Id, Product2>();
            mappedProductData.putAll(productsData);

            // Calculate total capacity of prodcuts
            Decimal filledCapacity = 0.0;
            for (ConnectApi.CartItemResult cartItem : cartItems) {
                Id productId = cartItem.cartItem.productId;
                Decimal qunatity = Decimal.valueOf(cartItem.cartItem.quantity);
                Object productSize = mappedProductData.get(productId).get('Sdo_Scom_B2B_Shipping_Cubic_Size__c');
                Decimal convertedProductSize = (productSize == null ? 0 : Decimal.valueOf(productSize.toString()));
                filledCapacity = filledCapacity + (qunatity * convertedProductSize);
            }
            return filledCapacity;
            
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }
}