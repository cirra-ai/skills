Global with sharing class SDO_CMS_SingleComponentPicklist extends VisualEditor.DynamicPickList {
    // Sets default value to return in the list of the component for the cmsDisplayer LWC. 
    global override VisualEditor.DataRow getDefaultValue() {
        VisualEditor.DataRow defaultValue = new VisualEditor.DataRow('None', 'NONE');
            return defaultValue;
    }

    global override VisualEditor.DynamicPickListRows getValues() {
        VisualEditor.DynamicPickListRows myValues = new VisualEditor.DynamicPickListRows();
        // Adds default value to list
        myValues.addRow(getDefaultValue());
        VisualEditor.DataRow value1 = new VisualEditor.DataRow('Current Record', 'RECORDID');
        myValues.addRow(value1);
        SDO_Experience_ContentArticle__c[] articles = [SELECT Id, Name,External_Id__c FROM SDO_Experience_ContentArticle__c
        WITH SECURITY_ENFORCED];
        // Loops through Content Articles found
    
        for(SDO_Experience_ContentArticle__c article: articles){
            myValues.addRow(new VisualEditor.DataRow(article.Name, article.External_Id__c));
        }
            return myValues;
    }
}