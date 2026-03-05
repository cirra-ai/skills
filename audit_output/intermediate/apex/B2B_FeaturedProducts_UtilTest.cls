@IsTest
public with sharing class B2B_FeaturedProducts_UtilTest {
    
    /*
        Work the util methods
    */
    @isTest static void testAddingMessages() {

        Map<String, Object> responseMap = new Map<String, Object>();

        B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message('Error', 'Some error message', B2B_FeaturedProducts_Util.ERROR), null, responseMap);
        B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message('Error', 'Some error message', B2B_FeaturedProducts_Util.ERROR), 0, responseMap);

        B2B_FeaturedProducts_Util.addMessage(new B2B_FeaturedProducts_Util.Message('Error', 'Some error message', B2B_FeaturedProducts_Util.ERROR, true), 0, responseMap);

    }

    @IsTest static void testProductDetailWrapper() {

        B2B_FeaturedProducts_Util.ProductDetailWrapper pdw = new B2B_FeaturedProducts_Util.ProductDetailWrapper();
        pdw.id = '1234567890';
        pdw.name = 'Some Product';
        pdw.defaultImage = null;
        pdw.entitlement = null;
        pdw.fields = new Map<String, Object>();
        pdw.mediaGroups = new List<ConnectApi.ProductMediaGroup>();
        pdw.primaryProductCategoryPath = null;
        pdw.prices = new B2B_FeaturedProducts_Util.ProductPricingWrapper();
        pdw.sequence = 1;

    }

    @IsTest static void testProductPricingWrapper() {
        B2B_FeaturedProducts_Util.ProductPricingWrapper ppw = new B2B_FeaturedProducts_Util.ProductPricingWrapper();
        ppw.listPrice = '1.98';
        ppw.unitPrice = '2.98';
        ppw.pricebookEntryId = '1234567890';
    }

}