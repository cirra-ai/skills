public class Sdo_Scom_Auction_PricingService extends commercestorepricing.PricingService {
    public override commercestorepricing.PricingResponse processPrice(
        commercestorepricing.PricingRequest request
    ) {
        System.debug('Pricing Service Request: Process Price');
        System.debug(request);

        Id webstoreId = request.getWebStoreId();
        Id effectiveAccountId = request.getEffectiveAccountId();
        List<Id> productIds = getProductIdsFromPricingRequestItems(request);
        System.debug('Requested Pricing Products: ' + productIds);
        List<Id> auctionProductIds = filterAuctionProductIds(webstoreId, effectiveAccountId, productIds);
        System.debug('Auction Products: ' + auctionProductIds);
        if(auctionProductIds.size() == 0) {
            return super.processPrice(request);
        }

        Map<Id, Decimal> productPrices = Sdo_Scom_Auction_Service.getAuctionProductsPrices(auctionProductIds, webstoreId, effectiveAccountId);
        System.debug('Auction Products prices: ' + productPrices);

        commercestorepricing.PricingResponse response = getPricingResponse(productPrices);
        System.debug(response);
        return response;
    }

    public override commercestorepricing.TransactionalPricingResponse processTransactionalPrice(
        commercestorepricing.TransactionalPricingRequest request
    ) {
        System.debug('Pricing Service Request: Process Transactional Price');
        System.debug(request);
        commercestorepricing.TransactionalPricingResponse response = super.processTransactionalPrice(request);
        System.debug('Initial Response');
        System.debug(response);
        try {
            Id webstoreId = request.getWebStoreId();
            Id effectiveAccountId = request.getEffectiveAccountId();
            List<Id> productIds = getProductIdsFromTxnPricingResponseItems(response);
            System.debug('Requested Transactional Pricing Products: ' + productIds);
            List<Id> auctionProductIds = filterAuctionProductIds(webstoreId, effectiveAccountId, productIds);
            System.debug('Auction Products: ' + auctionProductIds);
            if(auctionProductIds.size() == 0) {
                System.debug(response);
                return response;
            }

            Map<Id, Decimal> productPrices = Sdo_Scom_Auction_Service.getAuctionProductsPrices(auctionProductIds, webstoreId, effectiveAccountId);
            System.debug('Auction Products prices: ' + productPrices);

            updateTransactionalPrices(response, productPrices);
        } catch(Exception e) {
            System.debug('Exception in Process Transactional Price: ' + e.getMessage());
        }
        System.debug(response);
        return response;
    }

    private List<Id> getProductIdsFromPricingRequestItems(commercestorepricing.PricingRequest request) {
        commercestorepricing.PricingRequestItemCollection pricingRequestItems = request.getPricingRequestItems();
        
        List<String> productIds = new List<String>();
        for (Integer i = 0; i < pricingRequestItems.size(); i++) {
            commercestorepricing.PricingRequestItem pricingRequestItem = pricingRequestItems.get(i);
            productIds.add((Id) pricingRequestItem.getProductId());
        }
        return productIds;
    }

    private List<Id> getProductIdsFromTxnPricingResponseItems(
        commercestorepricing.TransactionalPricingResponse response
    ) {
        commercestorepricing.TxnPricingResponseItemCollection txnItems = response.getTxnPricingResponseItems();
        
        List<String> productIds = new List<String>();
        for (Integer i = 0; i < txnItems.size(); i++) {
            commercestorepricing.TransactionalPricingResponseItem item = txnItems.get(i);
            productIds.add((Id) item.getProductId());
        }
        return productIds;
    }


    private List<Id> filterAuctionProductIds(Id webstoreId, Id effectiveAccountId, List<Id> productIds) {
        List<String> fields = new List<String>{'Family'};
        List<String> auctionProductIds = new List<String>();
        try {
            ConnectApi.ProductOverviewCollection productsCollection = ConnectApi.CommerceCatalog.getProducts(webstoreId, effectiveAccountId, productIds, null, fields, true);
            List<ConnectApi.ProductOverview> products = productsCollection.products;
            for (Integer i = 0; i < products.size(); i++) {
                ConnectApi.ProductOverview product = products.get(i);
                if(product.fields.get('Family') == 'Auction') {
                    auctionProductIds.add((Id) product.id);
                }
            }
        } catch(Exception e) {
            System.debug('Exception in filter auction products: ' + e.getMessage());
        }
        return auctionProductIds;
    }

    private commercestorepricing.PricingResponse getPricingResponse(Map<Id, Decimal> productPrices) {
        commercestorepricing.PricingResponse response = new commercestorepricing.PricingResponse('USD');
        for (Id productId : productPrices.keySet()) {
            Decimal price = productPrices.get(productId);
            commercestorepricing.PricingResponseItem responseItem = new commercestorepricing.PricingResponseItem(
                productId,
                null,
                null,
                price, //List Price
                price // Unit Price
            );
            response.addPricingResponseItem(responseItem);
        }
        return response;
    }

    private void updateTransactionalPrices(
        commercestorepricing.TransactionalPricingResponse response, Map<Id, Decimal> productPrices
    ) {
        System.debug('Updating Transactional prices for products: ' + productPrices);
        commercestorepricing.TxnPricingResponseItemCollection txnItems = response.getTxnPricingResponseItems();
        
        Decimal adjustmentInTotalPrice = 0.0;
        Decimal adjustmentInTotalAdjustedAmount = 0.0;
        for (Integer i = 0; i < txnItems.size(); i++) {
            commercestorepricing.TransactionalPricingResponseItem item = txnItems.get(i);
            Id productId = item.getProductId();
            Decimal price = productPrices.get(productId);
            System.debug('Product price: ' + price);
            if(price != null) {
                System.debug('Updating Transactional price for product id: ' + productId);
                Decimal qty = item.getQuantity();
                Decimal itemTotalPrice = price * qty;
                Decimal originalItemTotalPrice = item.getTotalPrice();
                Decimal originalItemTotalAdjustmentAmount = item.getTotalAdjustmentAmount();
                adjustmentInTotalPrice += (originalItemTotalPrice == null)
                    ? itemTotalPrice
                    : originalItemTotalPrice - itemTotalPrice;
                adjustmentInTotalAdjustedAmount += (originalItemTotalAdjustmentAmount == null || originalItemTotalAdjustmentAmount == 0.0)
                    ? 0.0
                    : originalItemTotalAdjustmentAmount - itemTotalPrice;
                item.setListPrice(price);
                item.setUnitPrice(price);
                item.setTotalPrice(itemTotalPrice);
                item.setTotalLineAmount(itemTotalPrice);
                item.setTotalAdjustmentAmount(
                    (originalItemTotalAdjustmentAmount == null || originalItemTotalAdjustmentAmount == 0.0)
                    ? 0.0
                    :itemTotalPrice
                );
            }
        }
        Decimal originalTotalAdjustmentAmount = response.getTotalAdjustmentAmount();
        response.setTotalAdjustmentAmount(
            originalTotalAdjustmentAmount == null
            ? adjustmentInTotalAdjustedAmount
            : originalTotalAdjustmentAmount - adjustmentInTotalAdjustedAmount
        );
        Decimal originalTotalProductAmount = response.getTotalProductAmount();
        
        response.setTotalProductAmount(
            originalTotalProductAmount == null
            ? adjustmentInTotalPrice
            : originalTotalProductAmount - adjustmentInTotalPrice
        );
        response.setTotalAmount(response.getTotalProductAmount());
        System.debug('Updating Transactional prices is complered');
    }
}