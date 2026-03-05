public class CartSwitcherController {

    @AuraEnabled(cacheable=false)
    public static List<CartWrapper> getCarts(String communityId, String effectiveAccountId) {
        String webstoreId = resolveCommunityIdToWebstoreId(communityId);
        
        List<WebCart> carts = [SELECT Id, Name, Order_Type__c, OwnerId, isSecondary, SDO_SCOM_Old_Owner__c, SDO_SCOM_Shared__c
                               FROM WebCart 
                               WHERE AccountId = :effectiveAccountId AND Status = 'Active' AND WebStoreId = :webstoreId];

        
        //TODO: for each cart return the cart summary to see which one is the primary
        List<CartWrapper> cartWrappers = new List<CartWrapper>();
        
        for (integer i=0; i<carts.size(); i++) {
            WebCart cart = carts[i];
            ConnectApi.CartSummary cartSummary = ConnectApi.CommerceCart.getCartSummary(webstoreId, effectiveAccountId, cart.Id);
            CartWrapper cw = new CartWrapper();
            cw.id = cart.Id;
            cw.cart = cart;
            cw.cartSummary = cartSummary;

            if (UserInfo.getUserId() == cart.OwnerId) {
              cw.ownedByCurrentUser = true;
            } else {
              cw.ownedByCurrentUser = false;
            }

            if (cart.SDO_SCOM_Old_Owner__c != null) {
              cw.ownershipTaken = true;
            } else {
              cw.ownershipTaken = false;
            }
            

            cw.isShared = cart.SDO_SCOM_Shared__c;
            cartWrappers.add(cw);
        }
        return cartWrappers;
    }
    
    @AuraEnabled(cacheable=false)
    public static ConnectApi.CartSummary createCart(String communityId, String effectiveAccountId, String cartName) {
        ConnectApi.CartInput cart = new ConnectApi.CartInput();
        cart.effectiveAccountId = effectiveAccountId;
        cart.isSecondary = true;
        cart.name = cartName;
        String webstoreId = resolveCommunityIdToWebstoreId(communityId);
        
        ConnectApi.CartSummary cartSummary = ConnectApi.CommerceCart.createCart(webstoreId, cart);
        
        return cartSummary;
    }
    
    @AuraEnabled(cacheable=false)
    public static ConnectApi.CommerceActionResult setPrimaryCart(String communityId, String effectiveAccountId, String cartId) {
        String webstoreId = resolveCommunityIdToWebstoreId(communityId);
        ConnectApi.CommerceActionResult result = ConnectApi.CommerceCart.makeCartPrimary(webstoreId, cartId, effectiveAccountId);
        return result;
    }

    @AuraEnabled(cacheable=false)
    public static void takeOwnership(String communityId, String effectiveAccountId, String cartId) {
        String webstoreId = resolveCommunityIdToWebstoreId(communityId);
        
        //first we make all the carts secondary
        List<WebCart> carts = [SELECT Id, Name, IsSecondary, Order_Type__c 
          FROM WebCart 
          WHERE AccountId = :effectiveAccountId AND Status = 'Active' AND WebStoreId = :webstoreId];
        for (WebCart cart : carts) {
          cart.isSecondary = true;
        }
        update carts;
        
        //set the ownership to the new user
        WebCart wc = [SELECT Id, isSecondary, OwnerId, SDO_SCOM_Old_Owner__c 
          FROM WebCart WHERE Id = :cartId][0];
        String oldOwner = wc.OwnerId;
        wc.SDO_SCOM_Old_Owner__c = oldOwner;
        wc.OwnerId = UserInfo.getUserId();
        update wc;

        //share the cart with the old user
        /*
        if (oldOwner != UserInfo.getUserId()) {
          WebCartShare wcShare = new WebCartShare();
          wcShare.ParentId = wc.Id;
          wcShare.AccessLevel = 'edit';
          wcShare.UserOrGroupId = oldOwner;
          wcShare.RowCause = Schema.WebCartShare.RowCause.Manual;
          insert wcShare;
        }
        */

        //we set this cart as the primary
        ConnectApi.CommerceActionResult result = ConnectApi.CommerceCart.makeCartPrimary(webstoreId, cartId, effectiveAccountId);
    }

    @AuraEnabled(cacheable=false)
    public static void shareCart(String communityId, String effectiveAccountId, String cartId) {
        //set the cart as shared, the sharing rules will be created in the trigger
        WebCart cart = [SELECT Id, SDO_SCOM_Shared__c FROM WebCart WHERE Id = :cartId][0];
        cart.SDO_SCOM_Shared__c = true;
        update cart;
    }

    @AuraEnabled(cacheable=false)
    public static void releaseOwnership(String communityId, String effectiveAccountId, String cartId) {        
        //set the ownership to the new user and make the card secondary
        WebCart wc = [SELECT Id, isSecondary, OwnerId, SDO_SCOM_Old_Owner__c, SDO_SCOM_Shared__c 
          FROM WebCart WHERE Id = :cartId][0];
        String currentOwner = wc.OwnerId;
        wc.OwnerId = wc.SDO_SCOM_Old_Owner__c;
        wc.SDO_SCOM_Old_Owner__c = null;
        wc.isSecondary = true;
        wc.SDO_SCOM_Shared__c = false;
        update wc;

        //adding a sharing rule to keep visibility on the cart for the current user
        /*
        WebCartShare wcShare = new WebCartShare();
        wcShare.ParentId = wc.Id;
        wcShare.AccessLevel = 'edit';
        wcShare.UserOrGroupId = UserInfo.getUserId();
        wcShare.RowCause = Schema.WebCartShare.RowCause.Manual;
        insert wcShare;
        */
    }
    
    @AuraEnabled(cacheable=false)
    public static void deleteCart(String communityId, String effectiveAccountId, String cartId) {
        String webstoreId = resolveCommunityIdToWebstoreId(communityId);
		ConnectApi.CommerceCart.deleteCart(webstoreId, effectiveAccountId, cartId);
    }
    
    public class CartWrapper {
        @AuraEnabled
        public String id {get; set;}
        @AuraEnabled
        public WebCart cart {get; set;}
        @AuraEnabled
        public Boolean ownedByCurrentUser {get; set;}
        @AuraEnabled
        public Boolean ownershipTaken {get; set;}
        @AuraEnabled
        public Boolean isShared {get; set;}
        @AuraEnabled
        public ConnectApi.CartSummary cartSummary {get; set;}
    }
    
    /**
     * Util class to get the webstore id
     */
    private static Map<String, String> communityIdToWebStoreIdCache = new Map<String, String>();
    
    public static String resolveCommunityIdToWebstoreId(String communityId) {
    if (communityIdToWebStoreIdCache.containsKey(communityId)) {
      return communityIdToWebStoreIdCache.get(communityId);
    } else {
      String webStoreId = [
        SELECT WebStoreId
        FROM WebStoreNetwork
        WHERE NetworkId = :communityId
        WITH SECURITY_ENFORCED
        LIMIT 1
      ]
      .WebStoreId;
      communityIdToWebStoreIdCache.put(communityId, webStoreId);
      return webStoreId;
    }
  }
}