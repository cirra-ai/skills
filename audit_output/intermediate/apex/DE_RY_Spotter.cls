public without sharing class DE_RY_Spotter {
    public class customException extends Exception {} 
    public DE_RY_Spotter() {

    }

    @AuraEnabled (cacheable=false)
    public static String getUserAccountID() {
        String userId = UserInfo.getUserId();
        String contactId = [SELECT ContactId FROM User WHERE Id = :userId].ContactId;
        // return Account Id for Buyer
        if (contactId != null ) {
            return [SELECT AccountId FROM Contact WHERE id=:contactId].AccountId;
        }else { // return default Account Id if user is an Admin
            return [SELECT AccountId FROM Contact WHERE Name Like '%Lauren Bailey%'].AccountId;
        }
    }

    @AuraEnabled
    public static List<Spotter_Configuration__c> getAllConfigurations(){
        try {
            return [Select Id, Name from Spotter_Configuration__c order by CreatedDate DESC];
        } catch (Exception e) {
            throw new CustomException(e.getMessage());
        }
    }

    @AuraEnabled
    public static Spotter_Configuration__c createConfigRecord(String name, Id documentId){
        try {
            Spotter_Configuration__c config = new Spotter_Configuration__c();
            config.Name = name;
            config.Image_URL__c = getPublicDistURL(documentId);
            insert config;
            return config;
        } catch (Exception e) {
            throw new CustomException(e.getMessage());
        }
    }

    @AuraEnabled
    public static string changeImage(Id configId,  Id documentId){
        try {
            string imgUrl = getPublicDistURL(documentId);
            Spotter_Configuration__c config = new Spotter_Configuration__c();
            config.Id = configId;
            config.Image_URL__c = imgUrl;
            update config;
            return imgUrl;
        } catch (Exception e) {
            throw new CustomException(e.getMessage());
        }
    }

    @AuraEnabled
    public static string getPublicDistURL(Id documentId){
        try {
            ContentVersion cv = [SELECT Id,VersionData,ContentDocument.Title FROM ContentVersion WHERE ContentDocumentId = :documentId LIMIT 1];

            ContentDistribution cd = new ContentDistribution();
            cd.Name = cv.ContentDocument.Title;
            cd.ContentVersionId = cv.id;
            cd.PreferencesAllowViewInBrowser= true;
            cd.PreferencesLinkLatestVersion=true;
            cd.PreferencesNotifyOnVisit=false;
            cd.PreferencesPasswordRequired=false;
            cd.PreferencesAllowOriginalDownload= true;
            insert cd;
            
            //Download URL can be pass as parameter to holding frames
            return [SELECT Id,ContentDownloadUrl FROM ContentDistribution WHERE Id=:cd.Id].ContentDownloadUrl;
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }

    @AuraEnabled
    public static Spotter_Configuration__c getConfig(Id configId){
        try {
            return [Select Id, Name, Image_URL__c, Title__c, (Select Id, Name, Style_CSS__c, Spotter_Configuration__c, Product__c from Spotter_Hotspots__r Order By Name) from Spotter_Configuration__c where Id =: configId];
        } catch (Exception e) {
            throw new CustomException(e.getMessage());
        }
    }

    @AuraEnabled
    public static List<Spotter_Hotspot__c> saveHotspots(Spotter_Configuration__c configRec, List<Spotter_Hotspot__c> hotspots, List<Spotter_Hotspot__c> hotspotsToDelete){
        try {
            update configRec;
            if(hotspots.size()>0){
                upsert hotspots;
            }
            if(hotspotsToDelete.size() > 0){
                delete hotspotsToDelete;
            }
            return hotspots;
        } catch (Exception e) {
            throw new CustomException(e.getMessage());
        }
    }

    @AuraEnabled
    public static boolean deleteRecord(Id recordId){
        try {
            Database.DeleteResult dr = Database.delete(recordId);
            if(!dr.isSuccess()){
                throw new CustomException(dr.getErrors()[0].getMessage());
            }
            return dr.isSuccess();
        } catch (Exception e) {
            throw new CustomException(e.getMessage());
        }
    }

    public class configAndPricingDetails {
        @AuraEnabled
        public Spotter_Configuration__c config{get;set;}
        @AuraEnabled
        public ConnectApi.PricingResult pricelist{get;set;}
        @AuraEnabled
        public List<ConnectApi.ProductDetail> productImages {get;set;}
        @AuraEnabled
        public String relatedProductId {get;set;}

        public configAndPricingDetails(Spotter_Configuration__c config, ConnectApi.PricingResult pricelist, List<ConnectApi.ProductDetail> productImages, String relatedProductId){
            this.config = config;
            this.pricelist = pricelist;
            this.productImages = productImages;
            this.relatedProductId = relatedProductId;
        }
    }

    @AuraEnabled(cacheable=false)
    public static configAndPricingDetails getEmbedInfo(String spotterMode, Id configId, String communityId, String effectiveAccountId, String productRecordId){
        try {
            String webstoreId = resolveCommunityIdToWebstoreId(communityId);
            Spotter_Configuration__c currentConfig;
            ConnectApi.PricingResult priceListResponse = null;
            List<ConnectApi.ProductDetail> productImages = new List<ConnectApi.ProductDetail>();
            system.debug('spotterMode >>> ' + spotterMode + 'configId  >> ' + configId + ' communityId >> ' + communityId + ' effectiveAccountId >> ' + effectiveAccountId + ' webstoreId >> ' + webstoreId + 'productRecordId >> '+ productRecordId);
            if(spotterMode == 'Based on Current Product Record'){
                Product2 currentProduct = [Select Id, Spotter_Configuration__c from Product2 where Id =: productRecordId];
                configId = currentProduct.Spotter_Configuration__c;
            }
            if(configId != null){
                currentConfig = [Select Id, Name, Image_URL__c, Title__c, (Select Id, Name, Style_CSS__c, Spotter_Configuration__c, Product__c, Product__r.Name, Product__r.StockKeepingUnit from Spotter_Hotspots__r where Product__c != null and Product__r.IsActive = true Order By Name) from Spotter_Configuration__c where Id =: configId];
                List<Spotter_Hotspot__c> hotspots = currentConfig.Spotter_Hotspots__r;
                Set<Id> productIds = new Set<Id>();
                if(hotspots.size() > 0 && effectiveAccountId != null){
                    List<ConnectApi.PricingLineItemInput> pricingLineItems = new List<ConnectApi.PricingLineItemInput>();
                    for(Spotter_Hotspot__c spot : hotspots){
                        if(spot.Product__c != null && productIds.contains(spot.Product__c) == false){
                            productIds.add(spot.Product__c);
                            ConnectApi.PricingLineItemInput spot_pli = new ConnectApi.PricingLineItemInput();
                            spot_pli.productId = spot.Product__c;
                            pricingLineItems.add(spot_pli);
                        }
                    }
                    if(pricingLineItems.size() > 0){
                        ConnectApi.PricingInput pricingInput = new ConnectApi.PricingInput();
                        pricingInput.pricingLineItems = pricingLineItems;
                        /* system.debug('pricingLineItems');
                        system.debug(pricingLineItems);
                        system.debug('pricingInput');
                        system.debug(pricingInput); */
                        priceListResponse = ConnectApi.CommerceStorePricing.getProductPrices(webstoreId, effectiveAccountId, pricingInput);
                        system.debug(priceListResponse);
                    }
                    if(productIds.size() > 0){
                        List<String> mediaGroups = new List<String>();
                        for(Id prodId : productIds){                    
                            try { 
                                productImages.add(ConnectApi.CommerceCatalog.getProduct(
                                    webstoreId,
                                    String.valueOf(prodId),
                                    effectiveAccountId,
                                    null,
                                    false,
                                    mediaGroups,
                                    false,
                                    true,
                                    false
                                ));
                            } catch(ConnectApi.NotFoundException e) {
                                System.debug('Exception: ' + e.getMessage());
                                System.debug('Effective account is not entitled to this product: ' + prodId);
                            }
                        }
                        system.debug(productImages);
                    }
                }
            }
            return new configAndPricingDetails(currentConfig, priceListResponse, productImages, productRecordId);
        } catch (Exception e) {
            throw new CustomException(e.getMessage());
        }
    }

    public static String resolveCommunityIdToWebstoreId(String communityId) {
        try {
            String webStoreId = [
            SELECT WebStoreId
            FROM WebStoreNetwork
            WHERE NetworkId = :communityId
            LIMIT 1
            ]
            .WebStoreId;
            return webStoreId;
        } catch (Exception e) {
            throw new CustomException(e.getMessage());
        }
    }
}