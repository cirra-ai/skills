public with sharing class Sdo_Scom_Auction_Cart_Service {
    private static List<WebCart> getActiveCartForUser(Id webStoreId, Id accountId, Id userId) {
        return [
            SELECT Id
            FROM WebCart
            WHERE OwnerId = :userId AND Status = 'Active' AND AccountId = :accountId AND WebStoreId = :webStoreId
        ];
    }

    private static void createDeliveryGroupForCart(Id cartId) {
        CartDeliveryGroup deliveryGroup = new CartDeliveryGroup();
        deliveryGroup.CartId = cartId;
        deliveryGroup.Name = 'Auction Delivery';
        try {
            insert deliveryGroup;
        } catch (Exception e) {
            System.debug('Exception in creating delivery group for cart: ' + cartId);
        }
    }

    private static WebCart createCartForUser(Id webStoreId, Id accountId, Id userId) {
        String cartName = 'Auction_Cart';
        String cartStatus = 'Active';
        WebCart webCart = new WebCart();
        webCart.AccountId = accountId;
        webCart.Name = cartName;
        webCart.OwnerId = userId;
        webCart.Status = cartStatus;
        webCart.WebStoreId = webStoreId;
        try {
            insert webCart;
            createDeliveryGroupForCart(webCart.get('Id').toString());
        } catch (Exception e) {
            System.debug('Exception in creating cart for auction: ' + e.getMessage());
        }
        return webCart;
    }

    private static Id getUserCartId(Id webStoreId, Id accountId, Id userId) {
        System.debug('Auction - Get cart for User: ' + userId);
        List<WebCart> activeCarts = getActiveCartForUser(webStoreId, accountId, userId);
        if(activeCarts.size() > 0) {
            return activeCarts.get(0).get('Id').toString();
        }
        System.debug('Auction - No active cart found for user: ' + userId);
        System.debug('Auction - creating new cart for user: ' + userId);
        WebCart newCart = createCartForUser(webStoreId, accountId, userId);
        Id cartId = newCart.get('Id').toString();
        if(cartId == null) {
            System.debug('Auction - creating new cart failed for user: ' + userId);
        }
        return cartId;
    }

    public static void addItemToCart(Id webStoreId, Id accountId, Id userId, Id productId) {
        Id cartId = getUserCartId(webStoreId, accountId, userId);
        if(cartId == null) {
            return;
        }
        ConnectApi.CartItemInput cartInput = new ConnectApi.CartItemInput();
        cartInput.productId = productId;
        cartInput.quantity = '1' ;
        cartInput.type = ConnectApi.CartItemType.PRODUCT;
        System.debug('Auction - Adding Product add to cart: ' + productId + ', ' + webStoreId + ', ' + accountId);
        try {
            ConnectApi.CartItem cartItem = ConnectApi.CommerceCart.addItemToCart(
                webStoreId,
                accountId,
                cartId,
                cartInput
            );
            System.debug('Auction - Product add to cart successfully: ' + cartItem);
        } catch (Exception e) {
            System.debug('Auction - Product add to cart failed:: ' + e.getMessage());
        }
    }
}