public with sharing class SDO_CMS_RetrieveSingleArticle {
    @AuraEnabled (cacheable = false)
    public static List<SDO_Experience_ContentArticle__c> getContentArticle(String externalId, String sfRecordId){
        string whereClause ='';
        string soqlQuery ='';
        List <SDO_Experience_ContentArticle__c> singleArticle = new List<SDO_Experience_ContentArticle__c>();
        // If the ExternalID = recordId that means the user selected the current Record ID for the ID 
        // If the SF Record ID is populated that means it's on a record page. 
            if(externalId =='RECORDID' && sfRecordId != null){
                whereClause ='Id = :sfRecordId';
            } else if (externalId != 'RECORDID'){
                whereClause ='External_Id__c = :externalId';
            }
        soqlQuery = 'SELECT Id, Name, External_Id__c, SDO_ArticleContent__c, SDO_CMS_PreviewContent__c,SDO_ImageURL__c FROM SDO_Experience_ContentArticle__c WHERE '+whereClause+' WITH SECURITY_ENFORCED LIMIT 1';
        singleArticle = database.query(soqlQuery);
        return singleArticle;
    }


@AuraEnabled (cacheable = false)
    public static List<SDO_Experience_ContentArticle__c> getArticlesFromCollection(String externalId){
        List <SDO_Experience_ContentArticle__c> articleCollection = new List<SDO_Experience_ContentArticle__c>();
        return [
            SELECT 
                Id, 
                Name,
                External_Id__c,
                SDO_ArticleContent__c,
                SDO_CMS_PreviewContent__c,
                SDO_ImageURL__c
            FROM SDO_Experience_ContentArticle__c
            WHERE SDO_CMS_ContentCollection__r.External_Id__c = :externalId AND SDO_CMS_ContentCollection__c != null
            WITH SECURITY_ENFORCED 
            LIMIT 3
            
        ];
    }
}