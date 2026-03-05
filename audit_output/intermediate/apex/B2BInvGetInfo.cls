public with sharing class B2BInvGetInfo {
  @AuraEnabled(cacheable=true)
  public static ConnectApi.ProductDetail getProduct(
    String communityId,
    String productId,
    String effectiveAccountId
  ) {
    // Lookup the webstore ID associated with the community
    String webstoreId = B2BInvUtils.resolveCommunityIdToWebstoreId(communityId);

    // https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_ConnectAPI_CommerceCatalog_static_methods.htm#apex_ConnectAPI_CommerceCatalog_static_methods
    return ConnectApi.CommerceCatalog.getProduct(
      webstoreId,
      productId,
      effectiveAccountID,
      null,
      false,
      null,
      false,
      true,
      false
    );
  }

  @AuraEnabled(cacheable=true)
  public static List<Product_Inventory__c> getInventory(string productId)
  {
    List<Product_Inventory__c> inv = [Select Id, Location__c, Status__c, Qty_Available__c, Message__c from Product_Inventory__c where Product__c = :productId];
    return inv;    
  }

  @AuraEnabled(cacheable=true)
  public static Boolean checkProductIsInStock(String productId) {
    List<Product_Inventory__c> productInventory = getInventory(productId);
    Boolean ret = false;
    for(Product_Inventory__c inv : productInventory)
    {
      if(inv.Status__c != 'No Stock')
      {
        ret = true;
      }
    }
    return ret;
  }

  @AuraEnabled
  public static ConnectApi.CartSummary getCartSummary(
    String communityId,
    String effectiveAccountId
  ) {
    // Lookup the webstore ID associated with the community
    String webstoreId = B2BInvUtils.resolveCommunityIdToWebstoreId(communityId);

    //'current' is available in version 50.0 and later and indicates a cart with a status that isn’t Closed or PendingDelete
    //This is important for the product detail page since we are using the cart summary to check if the status is "Processing" or "Checkout"
    String activeCartOrId = 'current';

    // https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_ConnectAPI_CommerceCart_static_methods.htm
    return ConnectApi.CommerceCart.getCartSummary(
      webstoreId,
      effectiveAccountId,
      activeCartOrId
    );
  }

  @AuraEnabled
  public static ConnectApi.CartItem addToCart(
    String communityId,
    String productId,
    String quantity,
    String effectiveAccountId
  ) {
    // Lookup the webstore ID associated with the community
    String webstoreId = B2BInvUtils.resolveCommunityIdToWebstoreId(communityId);

    ConnectApi.CartItemInput cartInput = new ConnectApi.CartItemInput();
    cartInput.productId = productId;
    cartInput.quantity = quantity;
    cartInput.type = ConnectApi.CartItemType.PRODUCT;

    // https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_ConnectAPI_CommerceCart_static_methods.htm#apex_ConnectAPI_CommerceCart_static_methods
    return ConnectApi.CommerceCart.addItemToCart(
      webstoreId,
      effectiveAccountId,
      'active',
      cartInput
    );
  }

  @AuraEnabled
  public static ConnectApi.Wishlist createAndAddToList(
    String communityId,
    String productId,
    String wishlistName,
    String effectiveAccountId
  ) {
    // Lookup the webstore ID associated with the community
    String webstoreId = B2BInvUtils.resolveCommunityIdToWebstoreId(communityId);

    // Store the product in a WishlistItemInput to pass to the Wishlist
    ConnectApi.WishlistItemInput wishlistItemInput = new ConnectApi.WishlistItemInput();
    wishlistItemInput.productId = productId;

    //Create a wishlistInput to be created
    ConnectApi.WishlistInput wishlistInput = new ConnectApi.WishlistInput();
    wishlistInput.name = wishlistName;
    wishlistInput.products = new List<ConnectApi.WishlistItemInput>{
      wishlistItemInput
    };

    // https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_ConnectAPI_CommerceWishlist_static_methods.htm#apex_ConnectAPI_CommerceWishlist_static_methods
    return ConnectApi.CommerceWishlist.createWishlist(
      webstoreId,
      effectiveAccountId,
      wishlistInput
    );
  }

  @AuraEnabled(cacheable=true)
  public static ConnectApi.ProductPrice getProductPrice(
    String communityId,
    String productId,
    String effectiveAccountId
  ) {
    // Lookup the webstore ID associated with the community
    String webstoreId = B2BInvUtils.resolveCommunityIdToWebstoreId(communityId);

    // https://developer.salesforce.com/docs/atlas.en-us.apexcode.meta/apexcode/apex_ConnectAPI_CommerceStorePricing_static_methods.htm#apex_ConnectAPI_CommerceStorePricing_static_methods
    return ConnectApi.CommerceStorePricing.getProductPrice(
      webstoreId,
      productId,
      effectiveAccountId
    );
  }
}