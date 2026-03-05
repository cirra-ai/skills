Global with sharing class SDO_CMS_RetrieveCollectionList extends VisualEditor.DynamicPickList  {

    // Sets default value to return in the list of the component for the cmsDisplayer LWC. 
            global override VisualEditor.DataRow getDefaultValue() {
                VisualEditor.DataRow defaultValue = new VisualEditor.DataRow('None', 'NONE');
                    return defaultValue;
            }
    
            global override VisualEditor.DynamicPickListRows getValues() {
                VisualEditor.DynamicPickListRows myValues = new VisualEditor.DynamicPickListRows();
                // Adds default value to list
                    myValues.addRow(getDefaultValue());
                        SDO_Experience_ContentCollection__c[] articles = [SELECT Id, Name,External_ID__c FROM SDO_Experience_ContentCollection__c
                        WITH SECURITY_ENFORCED];
                // Loops through Content Collection(s) found
            
                for(SDO_Experience_ContentCollection__c article: articles){
                    myValues.addRow(new VisualEditor.DataRow(article.Name, article.External_ID__c));
                }
                    return myValues;
            }
    
        }