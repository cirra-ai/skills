global inherited sharing class D2CLookupFieldsPickList extends VisualEditor.DynamicPickList {

    VisualEditor.DesignTimePageContext context;
    global D2CLookupFieldsPickList(VisualEditor.DesignTimePageContext context) {
        this.context = context;
    }

    global override boolean isValid(Object attr) {
    return true;
    }

    global override VisualEditor.DataRow getDefaultValue(){
        VisualEditor.DataRow defaultValue = new VisualEditor.DataRow('Id', 'Id');
       return defaultValue;
    }


     global override VisualEditor.DynamicPickListRows getValues() {
         VisualEditor.DynamicPickListRows sObjectFields = new VisualEditor.DynamicPickListRows();
       if (context.entityName <> null) {
           Schema.DescribeSobjectResult[] desObjectResults = Schema.describeSObjects(new String[]{context.entityName});
           Schema.DescribeSObjectResult desObjectResult = desObjectResults[0];
           // System.debug('Display object ###### : '+ desObjectResults[0].getName());
           for(Schema.SobjectField strFld : desObjectResult.fields.getMap().Values()) {
                Schema.DescribeFieldResult dfr = strFld.getDescribe();
                //########################
                // Retrieve current object and fields from the list
                sObjectFields.addRow(new VisualEditor.DataRow(dfr.getLabel(), desObjectResults[0].getName()+'.'+dfr.getName()));  
            //   System.debug('Display ###### name: '+ new VisualEditor.DataRow(dfr.getLabel(), dfr.getName()));
           }
       }

       return sObjectFields;
    } 

}