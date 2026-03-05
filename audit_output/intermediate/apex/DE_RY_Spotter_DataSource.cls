global without sharing class DE_RY_Spotter_DataSource extends VisualEditor.DynamicPickList{

    public List<Spotter_Configuration__c> allConfigs;
    String naMessage = 'None Available';

    global DE_RY_Spotter_DataSource(){
        allConfigs = [Select Id, Name from Spotter_Configuration__c order by CreatedDate DESC];
    }

    global override VisualEditor.DataRow getDefaultValue(){
        VisualEditor.DataRow defaultValue;
        if (allConfigs.size() > 0) {
            defaultValue = new VisualEditor.DataRow(
                (string) allConfigs[0].get('Name'),
                (string) allConfigs[0].get('Id')
            );
        } else {
            defaultValue = new VisualEditor.DataRow(naMessage, 'None');
        }
        return defaultValue;
    }

    global override VisualEditor.DynamicPickListRows getValues() {
        VisualEditor.DynamicPickListRows myValues = new VisualEditor.DynamicPickListRows();
        if(allConfigs.size() > 0){
            for (Spotter_Configuration__c config : allConfigs) {
                myValues.addRow(
                    new VisualEditor.DataRow(
                    string.valueOf(config.Name),
                    string.valueOf(config.Id)
                    )
                );
            }
        }else {
            myValues.addRow(new VisualEditor.DataRow(naMessage, 'None'));
        }
        return myValues;
    }

}