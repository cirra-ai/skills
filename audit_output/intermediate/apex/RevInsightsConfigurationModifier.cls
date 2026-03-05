public with sharing class RevInsightsConfigurationModifier extends wavetemplate.WavetemplateConfigurationModifier
{
    // *****  Main method upon wizard config retrieval ***** /
    public override void onConfigurationRetrieval(wavetemplate.WaveTemplateInfo template)
     {
        setHistoricalAmountFields(template);
        checkForecastSettings(template);
        hasOpportunitySplits(template);
        hasCollabForecast(template);
        hasOpptySplitTypes(template);
     }


    private void hasOpportunitySplits(wavetemplate.WaveTemplateInfo template)
      {
          Schema.SObjectType splittypes = Schema.getGlobalDescribe().get('OpportunitySplitType');
          if (splittypes == null) {
            System.debug('OpportunitySplitType doesn\'t exist in the org.');
            template.getVariables().get('Has_OpportunitySplits').setComputedValue('No');
          }
          else {
            String query = 'SELECT DeveloperName, MasterLabel, SplitField, SplitEntity FROM OpportunitySplitType WHERE IsActive = true AND IsTotalValidated = true AND SplitEntity = \'Opportunity\'';
            try {
              List<SObject> activeSplitTypes = Database.query(query);
              if (activeSplitTypes.isEmpty()) {
                System.debug('No active 100% split types for opportunity');
                template.getVariables().get('Has_OpportunitySplits').setComputedValue('No');
              }
              else {
                  template.getVariables().get('Has_OpportunitySplits').setComputedValue('Yes');
              }
            }
            catch (Exception e) {
              System.debug('something went wrong, no splits:' + e);
            }
          }
    }
    
    private void hasCollabForecast(wavetemplate.WaveTemplateInfo template) {
        List<String> typeList = new List<String>();

        // uncomment for file based templates, Do not use in BPO
        // Map<String,Object> forecastingTypes = java:wave.template.extension.TemplateRevenueInsightsApexUtils.getForecastingTypesAllowCustomAmountAndSplits();
        // for (String key : forecastingTypes.keySet()) {
        //      typeList.add(key);
        // }

        // uncomment for BPOs, Do not use in file based template
        Schema.SObjectType forecastingTypeTest = Schema.getGlobalDescribe().get('ForecastingType');
        if (forecastingTypeTest != null) {
            String typeQuery = 'SELECT Id FROM ForecastingType WHERE IsActive = true LIMIT 4';
            List<sObject> types = database.query(typeQuery);
            for (sObject t : types) {
                String bpoTypes = (String)t.get('Id');
                typeList.add(bpoTypes);
            }
        }

        System.debug(typeList);

        // uncomment for file based
        // Schema.SObjectType targetTypeP = Schema.getGlobalDescribe().get('Opportunity__hd');

        List<String> forecastNames = new List<String>();
        for (String type : typeList) {
            List<sObject> typeNames = Database.query('SELECT DeveloperName FROM ForecastingType WHERE Id = :type');
            for (sObject name : typeNames) {
                String forecastName = (String)name.get('DeveloperName');
                // for BPO
                forecastNames.add(forecastName);

                // for file based uncomment below
                // String amountField = forecastingTypes.get((String)name.get('Id')).toString();
                
                // if ((amountField.substringBefore('.') == 'Opportunity' && amountField.substringAfter('.') == 'Amount') || amountField.substringBefore('.') == 'OpportunitySplit') {
                //     forecastNames.add(forecastName + ' (' + amountField + ')');
                // }
                // if (targetTypeP != null && amountField.substringBefore('.') == 'Opportunity' && amountField.substringAfter('.') != 'Amount') {
                //     Map<String, Schema.SObjectField> fieldMap = targetTypeP.getDescribe().fields.getMap();
                //     for(Schema.SObjectField sfield: fieldMap.Values()) {
                //     schema.describefieldresult dfield = sfield.getDescribe();
                //     if (dfield.getName().contains(amountField.substringAfter('.') + '_hst')) {
                //         forecastNames.add(forecastName + ' (' + amountField + ')');
                //             }
                //     }
                // }
            }
        }

        System.debug(forecastNames);
        
        if (forecastNames.isEmpty()) {
            template.getVariables().get('ForecastingType_Names').setComputedValue('No Valid ForecastTypes');
        }
        else {
            template.getVariables().get('ForecastingType_Names').getVariableType().setEnums(forecastNames);
            template.getVariables().get('ForecastingType_Names').setComputedValue('OpportunityRevenue');
        }
    }

     private void hasOpptySplitTypes(wavetemplate.WaveTemplateInfo template) {
        List<String> typeList = new List<String>();
        try {
            Schema.SObjectType splitTypeTest = Schema.getGlobalDescribe().get('OpportunitySplitType');
            if (splitTypeTest != null) {
                String query = 'SELECT DeveloperName, MasterLabel, SplitField, SplitEntity FROM OpportunitySplitType WHERE IsActive = true AND IsTotalValidated = true AND SplitEntity = \'Opportunity\'';
                List<sObject> types = database.query(query);
                for (sObject t : types) {
                    //String splitTypeId = (String)t.get('Id');
                    String splitTypeDevName = (String)t.get('DeveloperName');
                    String splitTypeSplitField = (String)t.get('SplitField');
                    String splitEntity = (String)t.get('SplitEntity');
                    typeList.add(splitTypeDevName+' ('+splitEntity+'.'+splitTypeSplitField+')');
                }
                template.getVariables().get('OpptySplitTypes').getVariableType().setEnums(typeList);
                template.getVariables().get('OpptySplitTypes').setComputedValue(typeList[0]);
            }
        } catch (Exception e) { System.debug('something went wrong parsing OpportunitySplitTypes for role hierarchy:' + e); }
    }

    private void checkForecastSettings(wavetemplate.WaveTemplateInfo template) {
        template.getVariables().get('isQuarterlyForecastingPeriod').setComputedValue(true);
        template.getVariables().get('isCumulativeEnabled').setComputedValue(true);
    }

    private void setHistoricalAmountFields(wavetemplate.WaveTemplateInfo template) {
        Map<string, wavetemplate.VariableDefinition> variables = template.getVariables();
        wavetemplate.VariableDefinition historicalFields = variables.get('CustomHistoricalAmount');
        wavetemplate.VariableDefinition opptyAmount = variables.get('Opportunity_Amount');
        Map<String, Schema.SObjectField> opptyfieldMap = Schema.SObjectType.Opportunity.fields.getMap();
        String fieldOptions = opptyfieldMap.get('Amount').getDescribe().getLabel() + ',';

        List<object> enums = historicalFields.getVariableType().getItemsType().getEnums();

        Schema.SObjectType targetTypeP = Schema.getGlobalDescribe().get('Opportunity__hd');
        if (targetTypeP != null) {
        Map<String, Schema.SObjectField> fieldMap = targetTypeP.getDescribe().fields.getMap();

        enums.add(opptyfieldMap.get('Amount').getDescribe().getLabel());

        For(Schema.SObjectField sfield: fieldMap.Values()) {
            schema.describefieldresult dfield = sfield.getDescribe();

            if ((dfield.getType() == Schema.DisplayType.CURRENCY || dfield.getType() == Schema.DisplayType.DOUBLE) && dfield.getName().contains('_hst') && dfield.getName() != 'Amount__hst') {
            enums.add(dfield.getName().replace('_hst',''));
            fieldOptions = fieldOptions + ' ' + opptyfieldMap.get(dfield.getName().replace('_hst','')).getDescribe().getLabel() + ',';
            }
        }
        historicalFields.getVariableType().getItemsType().setEnums(enums);
        }
        fieldOptions = fieldOptions.left(fieldOptions.length() - 1);

        Set<string> excludes = new Set<string>{'Probability'};
        Schema.SObjectType opptyType = Schema.getGlobalDescribe().get('Opportunity');

        for (Schema.SObjectField opptyField : opptyType.getDescribe().fields.getMap().Values()) {
            if ((string.valueOf(opptyField.getDescribe().getType()) == 'DOUBLE' || string.valueOf(opptyField.getDescribe().getType()) == 'CURRENCY') && !enums.contains(opptyField.getDescribe().getName()) && opptyField.getDescribe().getName() != 'Amount' ) {
                excludes.add(opptyField.getDescribe().getName());
            }
        }

        opptyAmount.setExcludes(excludes);
        template.getVariables().get('CustomHistoricalAmount').setComputedValue(enums);
        template.getVariables().get('CustomHistoricalCheck').setLabel('Analytics has detected that Opportunity (' + fieldOptions + ')  field(s) support Historical Trending. Select one of those fields otherwise the app will use the standard Amount field for historical trend data');
    }
    

    private void selectedAmountField(wavetemplate.Answers answers) {
        Object selectedType;
        try {
            selectedType = (String) answers.get('ForecastingType_Names');            
            String forecastingOverride = (String) answers.get('Forecasting_Override');
            if (selectedType != 'No Valid ForecastTypes' && selectedType != null && forecastingOverride == 'Yes') {
                String objectName;
                String objectField;
                // ****************************************************************************************************
                // sometimes typeLabel comes back as the actual DeveloperName of the selected forecasting type and sometimes
                // it's the Ids of the available active Forecast Types
                // so maybe it's safer to just use selectedType as the DeveloperName value.
                // ****************************************************************************************************
                String typeLabel = String.valueOf(selectedType).substringBefore(' (');
                answers.put('Forecasting_Types', typeLabel);  
                if (String.valueOf(selectedType).substringBetween('(', ')') !=null) {
                    objectName = String.valueOf(selectedType).substringBetween('(', ')').substringBefore('.');
                    objectField = String.valueOf(selectedType).substringBetween('(', ')').substringAfter('.');
                }
                if (objectName == 'Opportunity') {
                    Map<String, Object> opptyAmount = new Map<String, Object>{
                            'sobjectName' => objectName,
                            'fieldName' => objectField
                    };
                    answers.put('Opportunity_Amount', opptyAmount);
                }
                if (objectName == 'OpportunitySplit') {
                    Map<String, Object> opptySplitAmount = new Map<String, Object>{
                        'sobjectName'=> objectName,
                        'fieldName' => objectField
                    };
                    answers.put('OpportunitySplit_Amount', opptySplitAmount);
                    ////////////////////////////////////////////////////////////////////
                    // determine the SplitField used
                    ////////////////////////////////////////////////////////////////////
                    //String forecastingTypeQuery = 'SELECT OpportunitySplitTypeId FROM ForecastingType WHERE DeveloperName = :selectedType LIMIT 1';
                    String forecastingTypeQuery = 'SELECT OpportunitySplitTypeId FROM ForecastingType WHERE DeveloperName = :typeLabel LIMIT 1';
                    List<ForecastingType> opptySplitTypeIds = database.query(forecastingTypeQuery);
                    String opptySplitTypeId;
                    for(ForecastingType f : opptySplitTypeIds){
                        opptySplitTypeId = f.OpportunitySplitTypeId;
                    }
                    if (!String.isBlank(opptySplitTypeId)) {
                        System.debug('Found an Id. opptySplitTypeId:'+opptySplitTypeId);
                        String splitFieldQuery = 'SELECT SplitField FROM OpportunitySplitType WHERE Id = :opptySplitTypeId LIMIT 1';
                        List<OpportunitySplitType> splitFields = database.query(splitFieldQuery);
                        if (!splitFields.isEmpty()) {
                            System.debug('splitField for Oppty:'+splitFields);
                            String splitField = '';
                            for(OpportunitySplitType s : splitFields){
                                splitField = s.SplitField;
                            }
                            Map<String, Object> opptyAmount = new Map<String, Object>{
                                'sobjectName' => 'Opportunity',
                                'fieldName' => splitField
                            };
                            answers.put('Opportunity_Amount', opptyAmount);
                                }
                    } else { System.debug('opptySplitTypeId is empty.'+opptySplitTypeId);}
                    ////////////////////////////////////////////////////////////////////
                    // end determine SplitField used
                    ////////////////////////////////////////////////////////////////////
                }
            } else {
                // role hierachy stuff. for when not using forecasting 
                // added wiz question for which oppty split type to base app off of
                String hasOpptySplits = (String) answers.get('Has_OpportunitySplits');
                String selectedOpptySplitTypeUnparsed = (String) answers.get('OpptySplitTypes');
                String selectedSplitField = String.valueOf(selectedOpptySplitTypeUnparsed).substringBetween('(', ')').substringAfter('.');
                if (hasOpptySplits == 'Yes' && selectedSplitField != null) {
                    Map<String, Object> opptyAmount = new Map<String, Object>{
                            'sobjectName' => 'Opportunity',
                            'fieldName' => selectedSplitField
                    };
                    answers.put('Opportunity_Amount', opptyAmount);
                }
            }
        } catch(Exception e){
            answers.put('cmError', 'selectedAmountField parse failed ' + selectedType + e);
        }
        // additional logic needs to go here if splits is selected. Should that go to a new variable? should we reuse the same variable and set both object and amount field? 

        // if historical trending is made a requirement, we need to check for it here.
    }
    
    
      private void setReconfigurePath(wavetemplate.WaveTemplateInfo template, wavetemplate.Answers answers)
      {
        
      }



    //*********************Validation Before APP Creation**************************************************
    // Executes when we click on Create-APP button
    public override void beforeAppCreate(wavetemplate.WaveTemplateInfo template, wavetemplate.Answers answers)
    {
        //processAutoInstallRequest(template, answers);
        selectedAmountField(answers);
    }

    public override void beforeAppUpdate(wavetemplate.WaveTemplateInfo template, String previousAppVersion, wavetemplate.Answers answers) {
        //processAutoInstallRequest(template, answers);
        selectedAmountField(answers);
    }
}