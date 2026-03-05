public with sharing class B2B_Moodboard_Util {
    
    public class ProductDetailWrapper {

        public String id {get; set;}
        public String name {get; set;}

        public ConnectApi.ProductMedia defaultImage {get; set;}
        public ConnectApi.ProductEntitlement entitlement {get; set;}
        public Map<String, Object> fields {get; set;}
        public List<ConnectApi.ProductMediaGroup> mediaGroups {get; set;}
        public ConnectApi.ProductCategoryPath primaryProductCategoryPath {get; set;}

        public ProductPricingWrapper prices {get; set;}

        public Integer sequence {get; set;}
        public Integer top {get; set;}
        public Integer left {get; set;}
        public Integer height {get; set;}
        public Integer width {get; set;}
        public Integer zIndex {get; set;}

    }

    Public class ProductPricingWrapper {

        public String listPrice {get; set;}
        public String unitPrice {get; set;}

        public String pricebookEntryId {get; set;}

    }

}