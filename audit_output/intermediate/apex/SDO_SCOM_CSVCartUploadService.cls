public with sharing class SDO_SCOM_CSVCartUploadService {
    @AuraEnabled(cacheable=false)
    public static List<String> addToCart(
        Id webstoreId,
        Id effectiveAccountId,
        List<Map<String, String>> products
    ) {
        List<String> skus = new List<String>();
        Map<String, Integer> skusMap = new Map<String, Integer>();
        List<String> errors = new List<String>();
        for (Map<String, String>product : products) {
            String sku = product.get('productCode');
            Integer quantity = Integer.valueOf(product.get('quantity'));
            Integer existingQuantity = skusMap.get(sku);
            if(existingQuantity != null) {
                skusMap.put(sku, existingQuantity + quantity);
            } else {
                skusMap.put(sku, quantity);
                skus.add(sku);
            }
        }
        System.debug('SDO CSV Cart Upload: skus');
        System.debug(skus);
        System.debug('SDO CSV Cart Upload: skusMap');
        System.debug(skusMap);
        List<ConnectApi.ProductOverview> productOverviews = getProductsBySkus(webstoreId, effectiveAccountId, skus, errors);
        addItemsToCart(webstoreId, effectiveAccountId, productOverviews, skusMap, errors);
        System.debug('SDO CSV Cart Upload: Errors');
        System.debug(errors);
        return errors;
    }

    private static List<ConnectApi.ProductOverview> getProductsBySkus(
        Id webstoreId,
        Id effectiveAccountId,
        List<String> skus,
        List<String> errors
    ) {
        List<ConnectApi.ProductOverview> products = new List<ConnectApi.ProductOverview>();
        try {
            ConnectApi.ProductOverviewCollection productsCollection = ConnectApi.CommerceCatalog.getProducts(
                webstoreId,
                effectiveAccountId,
                null,
                skus,
                null,
                false,
                false
            );
            System.debug('SDO CSV Cart Upload: Product Collection');
            System.debug(productsCollection.products);
            for(ConnectApi.ProductOverview product: productsCollection.products) {
                String sku = product.sku;
                if(product.success) {
                    products.add(product);
                } else {
                    ConnectApi.ErrorResponse error = product.error;
                    errors.add(error.message);
                }
            }
        } catch(Exception e) {
            System.debug('SDO CSV Cart Upload: Exception is Getting Products Overview - ' + e.getMessage());
            throw new AuraHandledException(e.getMessage());
        }
        return products;
    }

    private static void addItemsToCart(
        Id webstoreId,
        Id effectiveAccountId,
        List<ConnectApi.ProductOverview> products,
        Map<String, Integer> skusMap,
        List<String> errors
    ) {
        List<ConnectApi.BatchInput> cartItems = buildCartItems(products, skusMap);
        System.debug('SDO CSV Cart Upload: Cart Items');
        System.debug(cartItems);
        try {
            String activeCartOrId = 'current';
            List<ConnectApi.BatchResult> batchResults = ConnectApi.CommerceCart.addItemsToCart(
                webstoreId,
                effectiveAccountId,
                activeCartOrId,
                cartItems
            );
            System.debug('SDO CSV Cart Upload: cartResponse');
            System.debug(batchResults);
            Integer batchResultsLength = batchResults.size();
            for(Integer i =0; i < batchResultsLength; i++) {
                ConnectApi.BatchResult batchResult = batchResults.get(i);
                if(!batchResult.isSuccess()) {
                    ConnectApi.ProductOverview product = products.get(i);
                    errors.add(product.sku + ': ' + batchResult.getErrorMessage());
                }
            }
        } catch(Exception e) {
            System.debug('SDO CSV Cart Upload: Exception is Adding Products to Cart: ' + e.getMessage());
            throw new AuraHandledException(e.getMessage());
        }
    }

    private static List<ConnectApi.BatchInput> buildCartItems(
        List<ConnectApi.ProductOverview> products,
        Map<String, Integer> skusMap
    ) {
        List<ConnectApi.BatchInput> cartItems = new List<ConnectApi.BatchInput>();
        for(ConnectApi.ProductOverview product: products) {
            String sku = product.sku;
            Id productId = product.id;
            String quantity = String.valueOf(skusMap.get(sku));
            ConnectApi.CartItemInput cartInput = new ConnectApi.CartItemInput();
            cartInput.productId = productId;
            cartInput.quantity = quantity;
            cartInput.type = ConnectApi.CartItemType.PRODUCT;
            cartItems.add(new ConnectApi.BatchInput(cartInput));
        }
        return cartItems;
    }
}