/**
 * @description       : Product Comparison Demo component dataservices
**/
public inherited sharing class PcProductComparisonDataServices {

    // Wrapper class to carry field information to the header
    class FieldSetInformation{
        @AuraEnabled public String fieldSetName;
        @AuraEnabled public String fieldSetLabel;
        @AuraEnabled public String fieldName;
        @AuraEnabled public String fieldLabel;
        public FieldSetInformation(String fieldSetName, String fieldSetLabel, String fieldName, String fieldLabel){
            this.fieldSetName = fieldSetName;
            this.fieldSetLabel = fieldSetLabel;
            this.fieldName = fieldName;
            this.fieldLabel = fieldLabel;
        }
    }

    /**
    * @description Fetch Field Set information as per the field sets passed in design resources
    * @param objectAPIName
    **/
    @AuraEnabled(cacheable=true)
    public static List<FieldSetInformation> getFieldSetInformation(String objectAPIName, String fieldsetListStr, String comparingFieldInfo){
        try {
            Set<String> fieldSetList = new Set<String>(fieldsetListStr.split(','));

            List<FieldSetInformation> fieldSetInfoList = new List<FieldSetInformation>();
            Map<String, Schema.FieldSet> fsMap = getFieldsByFieldset(objectAPIName);

            for(String fieldSetPassed : fieldSetList){
                if(fsMap.containsKey(fieldSetPassed)){
                    Schema.FieldSet fieldSetDesc =  fsMap.get(fieldSetPassed);
                    for(Schema.FieldSetMember fieldSetMem : getFieldsByFieldset(objectAPIName).get(fieldSetPassed).getFields()){
                        fieldSetInfoList.add(new FieldSetInformation(fieldSetDesc.getName(), fieldSetDesc.getLabel(), fieldSetMem.getFieldPath(), fieldSetMem.getLabel()));
                    }
                }
            }
            return fieldSetInfoList;
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }

    /**
    * @description Fetching all the fieldsets related to the object passed in params
    * @param objectAPIName
    * @return Map<String, Schema.FieldSet>
    **/
    public static Map<String, Schema.FieldSet> getFieldsByFieldset(String objectAPIName) {
        return Schema.getGlobalDescribe().get(objectAPIName).getDescribe().fieldSets.getMap();
    }


    /**
    * @description Fetching Sobject data based on query fields passed
    * @param objectAPIName
    * @param queryFields
    * @return List<sObject>
    **/
    @AuraEnabled (cacheable=false)
    public static List<sObject> getAllObjectData(String objectAPIName, String queryFields, String orderByField, String searchTerm, String comparingField){

        System.debug('SELECT ' + queryFields + ' FROM ' +objectAPIName + ' WHERE ' + comparingField + ' LIKE \'%' + searchTerm + '%\' ORDER BY '+orderByField + ' LIMIT 5 ');
        try {
            if(searchTerm == null)
                return new List<sObject>();
            return Database.query('SELECT ' + queryFields + ' FROM ' +objectAPIName + ' WHERE ' + comparingField + ' LIKE \'%' + searchTerm + '%\' ORDER BY '+orderByField + ' LIMIT 5 ');
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }

    /**
    * @description Get the preselected product data
    * @param objectAPIName
    * @param queryFields
    * @param orderByField
    * @param searchTerm
    * @param comparingField
    * @return List<sObject>
    **/
    @AuraEnabled
    public static sObject getPreSelectedObjectData(String objectAPIName, String queryFields, String orderByField, Id recordId, String comparingField){
        try {
            System.debug('SELECT ' + queryFields + ' FROM ' +objectAPIName + ' WHERE ' + ' Id=\'' + recordId + '\' ORDER BY '+orderByField + ' LIMIT 5 ');
            return Database.query('SELECT ' + queryFields + ' FROM ' +objectAPIName + ' WHERE ' + ' Id=\'' + recordId + '\' ORDER BY '+orderByField + ' LIMIT 5 ');
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }


    /**
    * @description Get the preselected product data
    * @param recordId
    * @return Boolean
    **/
    @AuraEnabled (cacheable=false)
    public static ConnectApi.ProductPrice getProductPrice(String communityId, String accountId, String recordId){

        System.debug('communityId > ' + communityId + ' accountId > ' + accountId + ' RecordId > ' + recordId);
        try{
            String webstoreId = resolveCommunityIdToWebstoreId(communityId);

            if(accountId == null){
                accountId = getUserAccountID();
            }

            return ConnectAPI.CommerceStorePricing.getProductPrice(webstoreId, recordId, accountId);
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }


    @AuraEnabled (cacheable=false)
    public static String getUserAccountID() {

        String userId = UserInfo.getUserId();

        System.debug('userId: ' + userId);
        String contactId = [SELECT ContactId FROM User WHERE Id = :userId].ContactId;
        if (contactId != null ) {
            System.debug('contactId: ' + contactId);
            return [SELECT AccountId FROM Contact WHERE id=:contactId].AccountId;
        }else {
            return [SELECT AccountId FROM Contact WHERE Name Like '%Lauren Bailey%'].AccountId;
        }
    }

    @AuraEnabled(cacheable=false)
    public static Boolean addProductToCart(String communityId, String accountId, String recordId, String quantity){
        try {
            String webstoreId = resolveCommunityIdToWebstoreId(communityId);
            System.debug('communityId > ' + communityId + '< accountId > ' + accountId + '< recordId > ' + recordId + '< quantity > ' + quantity + '< webstoreId > ' + webstoreId);

            if(accountId == null){
            	accountId = getUserAccountID();
            }

            ConnectAPI.CartItemInput cartItemInput = new ConnectAPI.CartItemInput();
            cartItemInput.quantity = quantity;
            cartItemInput.productId = recordId;
            cartItemInput.type = ConnectAPI.CartItemType.PRODUCT;

            ConnectAPI.CartItem cartItem = ConnectAPI.CommerceCart.addItemToCart(webstoreId, accountId, 'active', cartItemInput);
            return true;
        } catch (Exception e) {
            throw new AuraHandledException(e.getMessage());
        }
    }


    /*
        This method is used to convert the community Id to the web store Id.
    */
    @AuraEnabled
    public static String resolveCommunityIdToWebstoreId(String communityId) {
        if(communityId == null || communityId == '') {
            return null;
        }

        String webstoreId = null;

        List<WebStoreNetwork> wsnList = new List<WebStoreNetwork>();

        if(Schema.sObjectType.WebStoreNetwork.fields.WebStoreId.isAccessible()
        && Schema.sObjectType.WebStoreNetwork.fields.NetworkId.isAccessible()) {
            wsnList = [SELECT WebStoreId FROM WebStoreNetwork WHERE NetworkId = :communityId];
        }

        if(wsnList.size() > 0) {
            WebStoreNetwork wsn = wsnList.get(0);
            webstoreId = wsn.WebStoreId;
        }

        return webstoreId;
    }

}