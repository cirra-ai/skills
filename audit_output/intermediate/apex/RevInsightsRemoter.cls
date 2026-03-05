global with sharing class RevInsightsRemoter {

    global RevInsightsRemoter() {
    } // empty constructor

    // @SfdcOnly
    // @RemoteAction
    // global static Map<string, object> checkRecipeFieldAccess(Boolean hasProducts, Boolean hasActivities, Boolean hasSplits, Boolean hasCollaborativeForecasting, Boolean hasCollaborativeForecastingQuota) {
    //     List<string> errorMessages = new List<string>();
    //     List<string> fieldsWithAccess;
    //     List<string> fieldsWithNoAccess = new List<string>();
    //     List<string> fieldAsList;
    //     String objName;

    //     objName='OpportunityLineItem';
    //     fieldAsList = new String[] {'Id','OpportunityId','SortOrder','PricebookEntryId','Product2Id','ProductCode','Name','Quantity','TotalPrice','UnitPrice','ListPrice','Description','CreatedDate','LastModifiedDate'};
    //     fieldsWithAccess =  new List<String>((java:wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //     updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);

    //     objName='OpportunityHistory';
    //     fieldAsList = new String[] {'Id','OpportunityId','CreatedById','CreatedDate','StageName','Amount','CloseDate','ForecastCategory','IsDeleted'};
    //     fieldsWithAccess =  new List<String>((java:wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //     updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);

    //     objName='Opportunity';
    //     fieldAsList = new String[] {'Id','IsDeleted','AccountId','Name','Description','StageName','Amount','Probability','CloseDate','Type','NextStep','LeadSource','IsClosed','IsWon','ForecastCategory','ForecastCategoryName','HasOpportunityLineItem','Pricebook2Id','OwnerId','CreatedDate','LastModifiedDate','LastActivityDate','HasOpenActivity','HasOverdueTask'};
    //     fieldsWithAccess =  new List<String>((java:wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //     updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);

    //     objName='Account';
    //     fieldAsList = new String[] {'Id','MasterRecordId','Name','Type','ParentId','BillingStreet','BillingCity','BillingState','BillingPostalCode','BillingCountry','ShippingStreet','ShippingCity','ShippingState','ShippingPostalCode','ShippingCountry','Phone','PhotoUrl','Industry','AnnualRevenue','NumberOfEmployees','Description','OwnerId','CreatedDate','LastModifiedDate','LastActivityDate','LastViewedDate','AccountSource'};
    //     fieldsWithAccess =  new List<String>((java:wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //     updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);


    //     objName='User';
    //     fieldAsList = new String[] {'Id','Username','LastName','FirstName','Name','CompanyName','Division','Department','Title','Street','City','State','PostalCode','Country','Email','Phone','MobilePhone','Alias','IsActive','TimeZoneSidKey','UserRoleId','ReceivesInfoEmails','UserType','SmallPhotoUrl','ForecastEnabled'};
    //     fieldsWithAccess =  new List<String>((java:wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //     updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);

    //     objName='UserRole';
    //     fieldAsList = new String[] {'Id','Name','ParentRoleId','DeveloperName','ForecastUserId'};
    //     fieldsWithAccess =  new List<String>((java:wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //     updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);

    //     if(hasCollaborativeForecasting && hasCollaborativeForecastingQuota) {
    //         objName = 'ForecastingItem';
    //         fieldAsList = new String[]{'Id', 'OwnerId', 'PeriodId', 'ForecastingItemCategory', 'ForecastCategoryName',
    //                 'AmountWithoutAdjustments', 'AmountWithoutManagerAdjustment', 'ForecastAmount', 'IsAmount',
    //                 'HasAdjustment', 'HasOwnerAdjustment', 'ForecastingTypeId', 'AmountWithoutOwnerAdjustment'};
    //         fieldsWithAccess = new List<String>((java:
    //         wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //         updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);

    //         objName = 'ForecastingType';
    //         fieldAsList = new String[]{'Id', 'DeveloperName', 'MasterLabel', 'IsActive', 'IsQuantity', 'IsAmount'};
    //         fieldsWithAccess = new List<String>((java:
    //         wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //         updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);

    //         objName = 'ForecastingQuota';
    //         fieldAsList = new String[]{'Id', 'PeriodId', 'StartDate', 'ProductFamily', 'QuotaAmount', 'QuotaQuantity',
    //              'QuotaOwnerId', 'IsAmount', 'ForecastingTypeId'};
    //         fieldsWithAccess = new List<String>((java:
    //         wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //         updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);

    //         objName = 'Period';
    //         fieldAsList = new String[]{'Id', 'FiscalYearSettingsId', 'Type', 'StartDate', 'EndDate',
    //                 'IsForecastPeriod'};
    //         fieldsWithAccess = new List<String>((java:
    //         wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //         updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);
    //     }

    //     if(hasActivities) {
    //         objName = 'Task';
    //         fieldAsList = new String[]{'Id', 'WhoId', 'WhatId', 'Subject', 'ActivityDate', 'Status', 'Priority',
    //                 'IsHighPriority', 'OwnerId', 'Description', 'AccountId', 'IsClosed', 'CreatedDate', 'CreatedById',
    //                 'LastModifiedDate', 'CallDurationInSeconds', 'CallType', 'CallDisposition', 'CallObject',
    //                 'TaskSubtype'};
    //         fieldsWithAccess = new List<String>((java:
    //         wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //         updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);

    //         objName = 'Event';
    //         fieldAsList = new String[]{'Id', 'WhoId', 'WhatId', 'Subject', 'Location', 'ActivityDate',
    //                 'DurationInMinutes', 'EndDateTime', 'AccountId', 'OwnerId', 'ShowAs', 'CreatedDate', 'CreatedById',
    //                 'LastModifiedDate', 'EventSubtype'};
    //         fieldsWithAccess = new List<String>((java:
    //         wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //         updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);
    //     }

    //     if(hasSplits) {
    //         objName = 'OpportunitySplit';
    //         fieldAsList = new String[]{'Id', 'Split', 'CreatedDate', 'LastModifiedDate', 'OpportunityId',
    //                 'SplitOwnerId', 'SplitPercentage', 'SplitNote', 'SplitTypeId', 'SplitAmount'};
    //         fieldsWithAccess = new List<String>((java:
    //         wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //         updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);

    //         objName = 'OpportunitySplitType';
    //         fieldAsList = new String[]{'Id', 'DeveloperName', 'MasterLabel'};
    //         fieldsWithAccess = new List<String>((java:
    //         wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //         updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);
    //     }

    //     if(hasProducts) {
    //         objName = 'Product2';
    //         fieldAsList = new String[]{'Id', 'Name', 'ProductCode', 'Family'};
    //         fieldsWithAccess = new List<String>((java:
    //         wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //         updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);


    //         objName = 'PricebookEntry';
    //         fieldAsList = new String[]{'Id', 'Name', 'Pricebook2Id', 'Product2Id', 'UnitPrice', 'IsActive',
    //                 'UseStandardPrice', 'CreatedDate', 'LastModifiedDate', 'ProductCode', 'IsDeleted', 'IsArchived'};
    //         fieldsWithAccess = new List<String>((java:
    //         wave.template.extension.TemplateApexUtils.integUserGetAccessibleFields(objName)).keySet());
    //         updateErrorMessages(errorMessages, fieldsWithAccess, fieldAsList, objName);
    //     }

    //     if(errorMessages.size() > 0) {
    //         return new Map<String, Object>{
    //             'success' => false,
    //             'messages' => errorMessages,
    //             'errorMessages' => errorMessages
    //         };
    //     } else {
    //         return new Map<String, Object>{
    //             'success' => true,
    //             'messages' => errorMessages
    //         };
    //     }
    // }

    private static void updateErrorMessages(List<string> errorMessages, List<String> fieldsWithAccess, List<String> fieldsToCheck, String objName){
        List<String> fieldsWithNoAccess = new List<String>();
        for(String fieldName : fieldsToCheck){
            if(fieldsWithAccess.indexOf(fieldName) < 0){
                fieldsWithNoAccess.add(fieldName);
            }
        }
        if(fieldsWithNoAccess.size() > 0) {
            errorMessages.add(' Blocking issue - Integration User Has no access to ' + objName + ' : ' + String.join( fieldsWithNoAccess, ', ' ));
        }
    }

    @RemoteAction
    global static Map<string, object> dataOk() {
        boolean errorFlag = false;
        Integer accountCount = 0;
        Integer userCount = 0;
        Integer opportunityCount = 0;
        List<string> errorMessages = new List<string>();


        // Validate the following for these objects 1) Integration user has access 2) at least 1 record exists
        List<String> objectsToValidate = new list<String>{
                'Account',
                'User',
                'Opportunity'
        };

        try {
            for (String objectToValidate : objectsToValidate) {
                //Check for a access to Integration User
                if (!(boolean) wavetemplate.Access.integUserHasAccessToSObjectField(objectToValidate, 'Id')) {
                    errorMessages.add('The Analytics Integration User Profile does not have access to the ' + objectToValidate + ' Object.');
                    errorFlag = true;

                    // No need to try and do count if Analytics Integration user doesn't have access to object so continue
                    continue;
                }
                // Checking for presence of records in the objects
                if (doesRecordExist(objectToValidate) == 0) {
                    errorMessages.add('Revenue Insights requires at least one record in the ' + objectToValidate + ' Object');
                    errorFlag = true;
                }
            }
            if(hasRoleHierarchy().get('success') == false){
               errorMessages.add('Revenue Insights requires the use of Role Hierarchy');
               errorFlag = true;
            }
            if(hasActivities().get('success') == false){
               errorMessages.add('Revenue Insights requires the use of Event and Task');
               errorFlag = true;
            } else {
            }
        } catch (Exception e) {
            //really big orgs may fail on this query - incase they do let's assume they have accounts,opportunities,users
            accountCount = 1;
            userCount = 1;
            opportunityCount = 1;
        }
        // return the result
        if (errorFlag) {
            // return the error message
            return new Map<String, Object>{
                    'success' => false,
                    'messages' => errorMessages,
                    'errorMessages' => errorMessages
            };
        }

        return new Map<String, Object>{
                'success' => true,
                'messages' => new List<String>{
                        'Your org meets the minimum requirements for creating the app.'
                }
        };
    }

    private static Integer doesRecordExist(String objectName) {
        try {
            return database.countQuery('SELECT count() FROM ' + objectName + ' LIMIT 1');
        } catch (Exception e) {
            System.debug(e.getMessage());
        }
        return 0;
    }

    private static List<List<String>> getInitialMessages2d() {
        return new List<List<String>>{
                new List<String>(),
                new List<String>()
        };
    }


    public static boolean hasForecastHierarchy() {

        // check hierarchy setup
        // 1. at least one user with enabled forecast
        List<User> usersWithForecast = Database.query('SELECT Id FROM User WHERE ForecastEnabled = true LIMIT 1');
        if (usersWithForecast.isEmpty()) {
          system.debug('No user has ForecastEnabled');
          return false;
        }
        system.debug('User with ForecastEnabled: ' + usersWithForecast);

        // 2. at least one role has a forecast user
        List<UserRole> roleWithForecastUser = Database.query('SELECT Id FROM UserRole WHERE ForecastUserId != null LIMIT 1');
        if (roleWithForecastUser.isEmpty()) {
          system.debug('No role has a forecast user');
          return false;
        }
        system.debug('Role with ForecastUserId: ' + roleWithForecastUser);

        // 3. at least one role has a parent role
        List<UserRole> roleWithParent = Database.query('SELECT Id FROM UserRole WHERE ParentRoleId != null LIMIT 1');
        if (roleWithParent.isEmpty()) {
          system.debug('No role has a parent role');
          return false;
        }
        system.debug('Role with parent role: ' + roleWithParent);

        // 4. there's a forecast enabled user with role that has a parent role assigned to a forecast enabled user.
        // SELECT Id, Name FROM User WHERE ForecastEnabled = true
        // get a set of random roles assigned to a forecast user
        Set<Id> roleIdSet = new Set<Id>();
        for (User forecastUser: Database.query('SELECT Id, UserRoleId FROM User WHERE ForecastEnabled = true AND UserRoleId != null LIMIT 1000')) {
          roleIdSet.add(forecastUser.UserRoleId);
        }

        List<User> subOrdinates = Database.query('SELECT Id, UserRoleId FROM User WHERE ForecastEnabled = true AND UserRole.ParentRoleId IN :roleIdSet LIMIT 1');

        if (subOrdinates.isEmpty()) {
          system.debug('No forecasting role found to report to another forecasting role');
          return false;
        }
        system.debug('Role with parent that has collab: ' + subOrdinates);

        // if we got here, it's all good
        return true;
    }

    private static Map<String, Object> checkSplitsAndForecastPeriodConfiguration(){
        List<string> errorMessages = new List<string>();
        List<Object> variableSettings = new List<Object>();
        List<String> typeList = new List<String>();
        List<List<String>> messages2d = getInitialMessages2d();
        if(hasOpportunitySplits()){
            variableSettings.add(new Map<string, object>{
                    'name' => 'Has_OpportunitySplits',
                    'value' => 'Yes'
            });
        } else {
            variableSettings.add(new Map<string, object>{
                    'name' => 'Has_OpportunitySplits',
                    'value' => 'No'
            });
        }

        variableSettings.add(new Map<string, object>{
                'name' => 'isQuarterlyForecastingPeriod',
                'value' => hasQuarterlyForecast()
        });


        return new Map<String, Object>{
                'success' => true,
                'variableSettings' => variableSettings
        };
    }

    private static boolean hasOpportunitySplits() {
        Schema.SObjectType splittypes = Schema.getGlobalDescribe().get('OpportunitySplitType');
        if (splittypes == null) {
            return false;
        } else {
            String query = 'SELECT DeveloperName, MasterLabel, SplitField, SplitEntity FROM OpportunitySplitType WHERE IsActive = true AND IsTotalValidated = true AND SplitEntity = \'Opportunity\'';
            try {
                List<SObject> activeSplitTypes = Database.query(query);
                if (activeSplitTypes.isEmpty()) {
                    return false;
                } else {
                    return true;
                }
            } catch (Exception e) {
              System.debug('something went wrong, no splits:' + e);
            }
        }
        return false;
    }

    private static boolean hasQuarterlyForecast() {
        // Call Java class to get variable values
        boolean isQuarterlyForecastingPeriod = false;
        return isQuarterlyForecastingPeriod;
    }

    private static Map<String, Object> hasCollabForecast() {
      List<string> errorMessages = new List<string>();
      List<Object> variableSettings = new List<Object>();
      List<String> typeList = new List<String>();
      List<List<String>> messages2d = getInitialMessages2d();
      // where to put the message: 0 - has, 1 - doesn't have
      Integer msgIndex = 0;
      Integer quotaIndex = 0;
      Boolean hasDetectedCollabForecast = false;
      Boolean hasDetectedCollaborativeQuota = false;

      try {
        Schema.SObjectType forecastingType = Schema.getGlobalDescribe().get('ForecastingType');
        Schema.SobjectType forecastingItem = Schema.getGlobalDescribe().get('ForecastingItem');
        if (forecastingType != null && forecastingItem != null) {
            string forecastingTypeQuery = 'SELECT count() FROM ForecastingType WHERE IsActive = true LIMIT 1';
            string forecastingItemQuery = 'SELECT count() FROM ForecastingItem LIMIT 1';
            Integer forecastingTypeCount = database.countQuery(forecastingTypeQuery);
            Integer forecastingItemCount = database.countQuery(forecastingItemQuery);

            // uncomment for file based templates, Do not use in BPO
            // Map<String,String> forecastingTypes = java:wave.template.extension.TemplateRevenueInsightsApexUtils.getForecastingTypesAllowCustomAmountAndSplits();
            // for (String key : forecastingTypes.keySet()) {
            //     typeList.add(key);
            // }

            // uncomment for BPOs, Do not use in file based template
            String typeQuery = 'SELECT Id FROM ForecastingType WHERE IsActive = true LIMIT 4';
            List<sObject> types = database.query(typeQuery);
            for (sObject t : types) {
                String bpoTypes = (String)t.get('Id');
                typeList.add(bpoTypes);
            }

            if (!(boolean) wavetemplate.Access.integUserHasAccessToSObjectField('ForecastingType', 'Id')) {
                errorMessages.add('The Analytics Integration User Profile does not have access to the Forecasting Type Object.');
            }
            else if (!(boolean) wavetemplate.Access.integUserHasAccessToSObjectField('ForecastingItem', 'Id')) {
                errorMessages.add('The Analytics Integration User Profile does not have access to the Forecasting Item Object.');
            }
            else if (!typeList.isEmpty() && hasForecastHierarchy()) {
                hasDetectedCollabForecast = true;
                variableSettings.add(new Map<string, object>{
                        'name' => 'Has_CollaborativeForecasting',
                        'value' => 'Yes'
                });
                variableSettings.add(new Map<string, object>{
                        'name' => 'Forecasting_Types',
                        'value' => typeList
                });
                if (hasCollaborativeQuota()) {
                    hasDetectedCollaborativeQuota = true;
                    variableSettings.add(new Map<string, object>{
                        'name' => 'Has_CollaborativeForecastingQuota',
                        'value' => 'Yes'
                    });
                }
                else {
                    quotaIndex = 1;
                    variableSettings.add(new Map<string, object>{
                        'name' => 'Has_CollaborativeForecastingQuota',
                        'value' => 'No'
                    });
                    variableSettings.add(new Map<string, object>{
                        'name' => 'Forecasting_Override',
                        'value' => 'No'
                    });
                    errorMessages.add('No collaborativeForecastingQuota found');
                }
            }
            else {
                msgIndex = 1;
                quotaIndex = 1;
                variableSettings.add(new Map<string, object>{
                        'name' => 'Has_CollaborativeForecasting',
                        'value' => 'No'
                });
                variableSettings.add(new Map<string, object>{
                    'name' => 'Forecasting_Override',
                    'value' => 'No'
                });

                variableSettings.add(new Map<string, object>{
                    'name' => 'Has_CollaborativeForecastingQuota',
                    'value' => 'No'
                });
                variableSettings.add(new Map<string, object>{
                    'name' => 'Forecasting_Override',
                    'value' => 'No'
                });
                errorMessages.add('No collaborativeForecastingQuota or CollaborativeForecasting found');
            }
        } else {
            msgIndex = 1;
            quotaIndex = 1;
            variableSettings.add(new Map<string, object>{
                    'name' => 'Has_CollaborativeForecasting',
                    'value' => 'No'
            });
            variableSettings.add(new Map<string, object>{
                'name' => 'Forecasting_Override',
                'value' => 'No'
            });

            variableSettings.add(new Map<string, object>{
                    'name' => 'Has_CollaborativeForecastingQuota',
                    'value' => 'No'
            });
            variableSettings.add(new Map<string, object>{
                'name' => 'Forecasting_Override',
                'value' => 'No'
            });

            errorMessages.add('No ForecastingItem or ForecastingType accessible');
        }
      }
      catch (Exception e) {
        hasDetectedCollaborativeQuota = false;
        errorMessages.add(e.getMessage());
      }

      if (hasOpportunitySplits()) {
        messages2d[0].add('Opportunity Splits');  
      } else { messages2d[1].add('Opportunity Splits'); }

      messages2d[msgIndex].add('Collaborative Forecasting');
      messages2d[quotaIndex].add('Collaborative Forecasting Quota');

      return new Map<String, Object>{
              'success' => true,
              'variableSettings' => variableSettings,
              'messages2d' => messages2d
      };

    }

    public static boolean hasCollaborativeQuota() {

        Schema.SObjectType forecastQuota = Schema.getGlobalDescribe().get('ForecastingQuota');
        // Does the object exist
        if (forecastQuota == null) {
            return false;
        }

        string forecastQuotaQuery = 'SELECT Id FROM ForecastingQuota LIMIT 1';
        List <Object> forecastQuotaCount = Database.query(forecastQuotaQuery);

        if (!(boolean) wavetemplate.Access.integUserHasAccessToSObjectField('ForecastingQuota', 'Id')) {
            return false;
        }
        if (forecastQuotaCount.isEmpty()) {
            return false;
        }
        return true;
    }

private static Map<String, Object> hasActivities() {
      boolean hasDetectedActivities = false;
      List<string> errorMessages = new List<string>();
      List<Object> variableSettings = new List<Object>();
      List<List<String>> messages2d = getInitialMessages2d();
      // where to put the message: 0 - has, 1 - doesn't have
      Integer msgIndex = 0;
      try {
        Schema.SObjectType events = Schema.getGlobalDescribe().get('Event');
        Schema.SobjectType tasks = Schema.getGlobalDescribe().get('Task');
        if (events != null && tasks != null) {
            string eventsQuery = 'SELECT count() FROM Event LIMIT 1';
            string tasksQuery = 'SELECT count() FROM Task LIMIT 1';
            Integer eventsCount = database.countQuery(eventsQuery);
            Integer tasksCount = database.countQuery(tasksQuery);

            if (!(boolean) wavetemplate.Access.integUserHasAccessToSObjectField('Event', 'Id')) {
                errorMessages.add('The Analytics Integration User Profile does not have access to the Event Object.');
            }
            else if (!(boolean) wavetemplate.Access.integUserHasAccessToSObjectField('Task', 'Id')) {
                errorMessages.add('The Analytics Integration User Profile does not have access to the Task Object.');
            }
            else if (eventsCount > 0 && tasksCount > 0) {
                hasDetectedActivities = true;
                variableSettings.add(new Map<string, object>{
                        'name' => 'Has_Activities',
                        'value' => 'Yes'
                });
            }
            else {
                msgIndex = 1;
                variableSettings.add(new Map<string, object>{
                        'name' => 'Has_Activities',
                        'value' => 'No'
                });
                errorMessages.add('No Activities found');
            }
        }
        else {
            msgIndex = 1;
            variableSettings.add(new Map<string, object>{
                    'name' => 'Has_Activities',
                    'value' => 'No'
            });
            errorMessages.add('Event or Task object accessible');
        }
      }

      catch (Exception e) {
        errorMessages.add(e.getMessage());
      }

      if(hasDetectedActivities == true){
        messages2d[msgIndex].add('Event and Task');
        return new Map<String, Object>{
              'success' => true,
              'variableSettings' => variableSettings,
              'messages2d' => messages2d
        };
      } else {
        return new Map<String, Object>{
              'success' => false,
              'messages' => errorMessages,
              'errorMessages' => errorMessages
        };
      }
    }

private static Map<String, Object> hasProducts() {
      Boolean hasDetectedProducts = false;
      List<string> errorMessages = new List<string>();
      List<Object> variableSettings = new List<Object>();
      List<List<String>> messages2d = getInitialMessages2d();
      // where to put the message: 0 - has, 1 - doesn't have
      Integer msgIndex = 0;
      try {
        Schema.SObjectType products = Schema.getGlobalDescribe().get('Product2');
        if (products != null) {
            string queryLineItems = 'SELECT count() FROM OpportunityLineItem WHERE Product2Id != null AND PricebookEntryId != null LIMIT 1000';
            Integer countLineItems = database.countQuery(queryLineItems);

            if (countLineItems > 0) {
                hasDetectedProducts = true;
                variableSettings.add(new Map<string, object>{
                        'name' => 'Has_Products',
                        'value' => 'Yes'
                });
            }
            else {
                msgIndex = 1;
                variableSettings.add(new Map<string, object>{
                        'name' => 'Has_Products',
                        'value' => 'No'
                });
                errorMessages.add('No Products found');
            }
        }
        else {
                msgIndex = 1;
                variableSettings.add(new Map<string, object>{
                        'name' => 'Has_Products',
                        'value' => 'No'
                });
                errorMessages.add('No Product2 Object accessible');
        }
      }
      catch (Exception e) {
        errorMessages.add(e.getMessage());
      }

      messages2d[msgIndex].add('Opportunity Line Items');
      return new Map<String, Object>{
            'success' => true,
            'variableSettings' => variableSettings,
            'messages2d' => messages2d
      };

    }

private static Map<String, Object> hasMinimumDataForEDStory() {
      boolean errorFlag = false;
      List<string> errorMessages = new List<string>();
      List<Object> variableSettings = new List<Object>();
      List<List<String>> messages2d = getInitialMessages2d();
      // where to put the message: 0 - has, 1 - doesn't have
      Integer msgIndex = 0;
      try {
        Schema.SObjectType opps = Schema.getGlobalDescribe().get('Opportunity');
        if (opps != null) {
            string queryOpp = 'SELECT count() FROM Opportunity LIMIT 400';
            Integer countOpp = database.countQuery(queryOpp);

            string queryWon = 'SELECT count() FROM Opportunity WHERE IsWon = true LIMIT 25';
            Integer countWon = database.countQuery(queryWon);

            string queryLost = 'SELECT count() FROM Opportunity WHERE IsClosed = true AND IsWon = false LIMIT 25';
            Integer countLost = database.countQuery(queryLost);

            if (countOpp == 400 && countWon == 25 && countLost == 25) {
                variableSettings.add(new Map<string, object>{
                        'name' => 'Has_Minimum_Data_For_EDStory',
                        'value' => 'No'
                });
            }
            else {
                msgIndex = 1;
                variableSettings.add(new Map<string, object>{
                        'name' => 'Has_Minimum_Data_For_EDStory',
                        'value' => 'No'
                });
            }
        }
        else {
                msgIndex = 1;
                variableSettings.add(new Map<string, object>{
                        'name' => 'Has_Minimum_Data_For_EDStory',
                        'value' => 'No'
                });
        }
      }
      catch (Exception e) {
        System.debug('Something went wrong, not enough data for Likelihood_to_Win ED Story:' + e);
      }

      messages2d[msgIndex].add('Data for Likelihood_to_Win ED Story');
      return new Map<String, Object>{
              'success' => true,
              'variableSettings' => variableSettings,
              'messages2d' => messages2d
      };
    }

    public static Map<String, Object> hasCustomAddressFieldsEnabled() {
        boolean isSuccess = false;
        List<Object> variableSettings = new List<Object>();
        List<string> errorMessages = new List<string>();
        String message;
        try {
            //boolean orgHasCustomAddressFieldsEnabled = java:wave.template.extension.TemplateApexUtils.isCustomAddressFieldEnabled();
            // When using BPO based templates, we can't call internal java classes so
            // manually set orgHasReplicationEnabled = true
            boolean orgHasCustomAddressFieldsEnabled = false;
            System.debug('orgHasCustomAddressFieldsEnabled value is set to: ' + orgHasCustomAddressFieldsEnabled);
            if (orgHasCustomAddressFieldsEnabled) {
                isSuccess = false;
                message = 'Custom Address Fields (Beta feature) is enabled. Unfortunately, this feature is not compatible with Revenue Insights.';
                errorMessages.add(message);
                variableSettings.add(new Map<string, object>{
                        'name' => 'Has_CustomAddressFieldsEnabled',
                        'value' => 'Yes'
                });
            } else {
                isSuccess = true;
                message = 'Custom Address Fields (Beta feature) is not enabled.';
                variableSettings.add(new Map<string, object>{
                        'name' => 'Has_CustomAddressFieldsEnabled',
                        'value' => 'No'
                });
            }
        }
        catch (Exception e) {
            System.debug('Something went wrong, Custom Address Fields is enabled:' + e);
            isSuccess = false;
            message = 'Custom Address Fields (Beta feature) is enabled. Unfortunately, this feature is not compatible with Revenue Insights.';
            errorMessages.add(message);
            variableSettings.add(new Map<string, object>{
                    'name' => 'Has_CustomAddressFieldsEnabled',
                    'value' => 'Yes'
            });
        }
        return new Map<String, Object>{
                'success' => isSuccess,
                'variableSettings' => variableSettings,
                'messages' => new List<String>{message},
                'errorMessages' => errorMessages
            };
    }

    public static Map<String, Object> hasRoleHierarchy() {
      Boolean hasDetectedRoleHierarchy = false;
      List<String> errorMessages = new List<String>();
      List<Object> variableSettings = new List<Object>();
      List<List<String>> messages2d = getInitialMessages2d();
      String message;
      try {
        Integer RoleCount = 0;

        //Check for users with roles that have role parents
        RoleCount = Database.countQuery('SELECT count() FROM User WHERE userrole.parentRoleID != null');

        if (RoleCount > 0) {
          //Customer is using role hierarchy, so let's use it!!
          variableSettings.add(new Map<string, object>{
                  'name' => 'Has_RoleHierarchy',
                  'value' => 'Yes'
          });
          hasDetectedRoleHierarchy = true;
          messages2d[0].add('Role Hierarchy is enabled');
        } else {
          variableSettings.add(new Map<string, object>{
                  'name' => 'Has_RoleHierarchy',
                  'value' => 'No'
          });
          messages2d[0].add('Role Hierarchy is not enabled');
        }
      }

      catch (Exception e) {
        message = e.getMessage();
        errorMessages.add(message);
      }

      if(hasDetectedRoleHierarchy == true){
        return new Map<String, Object>{
              'success' => true,
              'variableSettings' => variableSettings,
              'messages2d' => messages2d
              //'messages' => new List<String>{message}
        };
      } else {
        return new Map<String, Object>{
              'success' => true,
              //'messages' => new List<String>{message},
              'errorMessages' => errorMessages,
              'variableSettings' => variableSettings,
              'messages2d' => messages2d
        };
      }
    }

    /*****2.Method to Autoscan and set fiscal******/
    private static Map<String, Object> setFiscal() {
        List<Object> variableSettings = new List<Object>();
        String offset;
        try {
            Integer months = [
                    SELECT
                            FiscalYearStartMonth
                    FROM
                            Organization
            ].FiscalYearStartMonth;

            Map<Integer, string> a = new Map<Integer, string>{
                    1 => '01 - January',
                    2 => '02 - February',
                    3 => '03 - March',
                    4 => '04 - April',
                    5 => '05 - May',
                    6 => '06 - June',
                    7 => '07 - July',
                    8 => '08 - August',
                    9 => '09 - September',
                    10 => '10 - October',
                    11 => '11 - November',
                    12 => '12 - December'
            };
            String monthOffset = a.get(months);
            system.debug('monthOffset is ' + monthOffset);
            variableSettings.add(new Map<string, object>{
                    'name' => 'Fiscal_Month',
                    'value' => monthOffset
            });
            offset = monthOffset;
            // set description? No.
            // template.getVariables().get('Fiscal_Month').setDescription('Wave has selected the month based on your Salesforce settings but you may override this value. If it is different than January, you also need to update the Quota dataset JSON file.');
        } catch (Exception e) {
            //just in case
            variableSettings.add(new Map<string, object>{
                    'name' => 'Fiscal_Month',
                    'value' => '01 - January'
            });
            offset = '01 - January';
        }
        return new Map<String, Object>{
                'success' => true,
                'variableSettings' => variableSettings,
                'messages' => new List<String>{
                        'Fiscal month is set to ' + offset.substring(5) + ', '
                }
        };
    }

    /**
    * Private method to initialize the Locale Mapping
    * @returns Map<String, Integer>
    */
    private static Map<String, Integer> initLocaleMap() {
        //add all mappings for Supported Locales and their Start Day offset here
        Map<String, Integer> mymap = new Map<String, Integer>();
        mymap.put('sq_AL', 6);
        mymap.put('ar_DZ', 6);
        mymap.put('ar_BH', 6);
        mymap.put('ar_EG', 0);
        mymap.put('ar_IQ', 0);
        mymap.put('ar_JO', 6);
        mymap.put('ar_KW', 6);
        mymap.put('ar_LB', 6);
        mymap.put('ar_LY', 6);
        mymap.put('ar_MA', 6);
        mymap.put('ar_OM', 6);
        mymap.put('ar_QA', 6);
        mymap.put('ar_SA', 6);
        mymap.put('ar_SD', 6);
        mymap.put('ar_SY', 6);
        mymap.put('ar_TN', 6);
        mymap.put('ar_AE', 6);
        mymap.put('ar_YE', 6);
        mymap.put('hy_AM', 0);
        mymap.put('az_AZ', 0);
        mymap.put('eu_ES', 0);
        mymap.put('be_BY', 0);
        mymap.put('bn_BD', 0);
        mymap.put('bs_BA', 0);
        mymap.put('bg_BG', 0);
        mymap.put('my_MM', 0);
        mymap.put('ca_ES_EURO', 1);
        mymap.put('ca_ES', 1);
        mymap.put('zh_CN_PINYIN', 0);
        mymap.put('zh_CN_STROKE', 0);
        mymap.put('zh_CN', 0);
        mymap.put('zh_HK_STROKE', 0);
        mymap.put('zh_HK', 0);
        mymap.put('zh_MO', 0);
        mymap.put('zh_SG', 0);
        mymap.put('zh_TW_STROKE', 0);
        mymap.put('zh_TW', 0);
        mymap.put('hr_HR', 1);
        mymap.put('cs_CZ', 1);
        mymap.put('da_DK', 1);
        mymap.put('nl_AW', 1);
        mymap.put('nl_BE', 1);
        mymap.put('nl_NL', 1);
        mymap.put('nl_SR', 1);
        mymap.put('dz_BT', 0);
        mymap.put('en_AG', 0);
        mymap.put('en_AU', 0);
        mymap.put('en_BS', 0);
        mymap.put('en_BB', 0);
        mymap.put('en_BZ', 0);
        mymap.put('en_BM', 0);
        mymap.put('en_BW', 0);
        mymap.put('en_CM', 0);
        mymap.put('en_CA', 0);
        mymap.put('en_KY', 0);
        mymap.put('en_ER', 0);
        mymap.put('en_FK', 0);
        mymap.put('en_FJ', 0);
        mymap.put('en_GM', 0);
        mymap.put('en_GH', 0);
        mymap.put('en_GI', 0);
        mymap.put('en_GY', 0);
        mymap.put('en_HK', 0);
        mymap.put('en_IN', 0);
        mymap.put('en_ID', 0);
        mymap.put('en_IE_EURO', 1);
        mymap.put('en_IE', 1);
        mymap.put('en_JM', 0);
        mymap.put('en_KE', 0);
        mymap.put('en_LR', 0);
        mymap.put('en_MG', 0);
        mymap.put('en_MW', 0);
        mymap.put('en_MY', 0);
        mymap.put('en_MU', 0);
        mymap.put('en_NA', 0);
        mymap.put('en_NZ', 0);
        mymap.put('en_NG', 0);
        mymap.put('en_PK', 0);
        mymap.put('en_PG', 0);
        mymap.put('en_PH', 0);
        mymap.put('en_RW', 0);
        mymap.put('en_SH', 0);
        mymap.put('en_WS', 0);
        mymap.put('en_SC', 0);
        mymap.put('en_SL', 0);
        mymap.put('en_SG', 0);
        mymap.put('en_SX', 0);
        mymap.put('en_SB', 0);
        mymap.put('en_ZA', 0);
        mymap.put('en_SZ', 0);
        mymap.put('en_TZ', 0);
        mymap.put('en_TO', 0);
        mymap.put('en_TT', 0);
        mymap.put('en_UG', 0);
        mymap.put('en_GB', 1);
        mymap.put('en_US', 0);
        mymap.put('en_VU', 0);
        mymap.put('et_EE', 1);
        mymap.put('fi_FI_EURO', 1);
        mymap.put('fi_FI', 1);
        mymap.put('fr_BE', 1);
        mymap.put('fr_CA', 0);
        mymap.put('fr_KM', 1);
        mymap.put('fr_FR_EURO', 1);
        mymap.put('fr_FR', 1);
        mymap.put('fr_GN', 1);
        mymap.put('fr_HT', 1);
        mymap.put('fr_LU', 1);
        mymap.put('fr_MR', 1);
        mymap.put('fr_MC', 1);
        mymap.put('fr_CH', 1);
        mymap.put('fr_WF', 1);
        mymap.put('ka_GE', 0);
        mymap.put('de_AT_EURO', 1);
        mymap.put('de_AT', 1);
        mymap.put('de_DE_EURO', 1);
        mymap.put('de_DE', 1);
        mymap.put('de_LU_EURO', 1);
        mymap.put('de_LU', 1);
        mymap.put('de_CH', 1);
        mymap.put('el_GR', 1);
        mymap.put('iw_IL', 0);
        mymap.put('hi_IN', 0);
        mymap.put('hu_HU', 1);
        mymap.put('is_IS', 1);
        mymap.put('in_ID', 1);
        mymap.put('ga_IE', 0);
        mymap.put('it_IT', 1);
        mymap.put('it_CH', 1);
        mymap.put('ja_JP', 0);
        mymap.put('kk_KZ', 0);
        mymap.put('km_KH', 0);
        mymap.put('ky_KG', 0);
        mymap.put('ko_KP', 0);
        mymap.put('ko_KR', 0);
        mymap.put('lo_LA', 0);
        mymap.put('lv_LV', 0);
        mymap.put('lt_LT', 1);
        mymap.put('lu_CD', 0);
        mymap.put('lb_LU', 0);
        mymap.put('mk_MK', 0);
        mymap.put('ms_BN', 0);
        mymap.put('ms_MY', 0);
        mymap.put('mt_MT', 0);
        mymap.put('ne_NP', 0);
        mymap.put('no_NO', 1);
        mymap.put('ps_AF', 0);
        mymap.put('fa_IR', 0);
        mymap.put('pl_PL', 1);
        mymap.put('pt_AO', 1);
        mymap.put('pt_BR', 0);
        mymap.put('pt_CV', 1);
        mymap.put('pt_MZ', 1);
        mymap.put('pt_PT', 1);
        mymap.put('pt_ST', 1);
        mymap.put('ro_MD', 1);
        mymap.put('ro_RO', 1);
        mymap.put('rm_CH', 0);
        mymap.put('rn_BI', 0);
        mymap.put('ru_RU', 1);
        mymap.put('sr_BA', 1);
        mymap.put('sr_RS', 0);
        mymap.put('sr_CS', 1);
        mymap.put('sh_BA', 1);
        mymap.put('sh_ME', 1);
        mymap.put('sh_CS', 1);
        mymap.put('sk_SK', 1);
        mymap.put('sl_SI', 1);
        mymap.put('so_DJ', 0);
        mymap.put('so_SO', 0);
        mymap.put('es_AR', 1);
        mymap.put('es_BO', 1);
        mymap.put('es_CL', 1);
        mymap.put('es_CO', 1);
        mymap.put('es_CR', 1);
        mymap.put('es_CU', 1);
        mymap.put('es_DO', 1);
        mymap.put('es_EC', 1);
        mymap.put('es_SV', 1);
        mymap.put('es_GT', 1);
        mymap.put('es_HN', 1);
        mymap.put('es_MX', 1);
        mymap.put('es_NI', 1);
        mymap.put('es_PA', 1);
        mymap.put('es_PY', 1);
        mymap.put('es_PE', 1);
        mymap.put('es_PR', 1);
        mymap.put('es_ES_EURO', 1);
        mymap.put('es_ES', 1);
        mymap.put('es_US', 0);
        mymap.put('es_UY', 1);
        mymap.put('es_VE', 1);
        mymap.put('sv_SE', 1);
        mymap.put('tl_PH', 0);
        mymap.put('tg_TJ', 0);
        mymap.put('ta_IN', 0);
        mymap.put('ta_LK', 0);
        mymap.put('th_TH', 0);
        mymap.put('ti_ET', 0);
        mymap.put('tr_TR', 1);
        mymap.put('uk_UA', 1);
        mymap.put('ur_PK', 0);
        mymap.put('uz_LATN_UZ', 0);
        mymap.put('vi_VN', 0);
        mymap.put('cy_GB', 0);
        mymap.put('yo_BJ', 0);

        return mymap;
    }

    private static Map<String, Object> aggregateResults(List<Map<String, Object>> resultList) {

        Boolean allGood = true;
        List<Map<String, Object>> variableSettings = new List<Map<String, Object>>();
        List<String> messages = new List<String>();
        List<String> errorMessages = new List<String>();
        List<List<String>> messages2d = new List<List<String>>();

        // iterate over the results
        for (Map<String, Object> result : resultList) {
            // if one failed all failed
            if (!((boolean) result.get('success'))) {
                allGood = false;
            }

            // aggregate the variable settings
            if (result.containsKey('variableSettings')) {
                for (Object s : (List<Object>) result.get('variableSettings')) {
                    variableSettings.add((Map<String, Object>) s);
                }
            }

            // and messages
            if (result.containsKey('messages')) {
                List<String> addedMessages = (List<String>) result.get('messages');
                if (result.containsKey('mergeWithPrevious')) {
                    messages[messages.size() - 1] += addedMessages[0];
                } else {
                    messages.addAll(addedMessages);
                }
            }

            // and errorMessages
            if (result.containsKey('errorMessages')) {
                List<String> addedErrorMessages = (List<String>) result.get('errorMessages');
                errorMessages.addAll(addedErrorMessages);
            }

            // and array of array of messages
            if (result.containsKey('messages2d')) {
                List<Object> resultMessages = (List<Object>) result.get('messages2d');
                // for each array in 2d array
                for (Integer i = 0; i < resultMessages.size(); i++) {
                    // incoming array bigger than what we have
                    if ((i + 1) > messages2d.size()) {
                        messages2d.add(new List<String>());
                    }
                    messages2d[i].addAll((List<String>) resultMessages[i]);
                }
            }
        }

        // flatten the messages2d into messages
        for (Integer i = 0; i < messages2d.size(); i++) {
            List<String> messageList = messages2d[i];
            messages.addAll((List<String>) messageList);
            if (i < messages2d.size() - 1) {
                // space between the lists - not for the last
                messages.add('');
            }
        }

        // aggregate the messages and variable settings
        return new Map<String, Object>{
            'success' => allGood,
            'messages' => messages,
            'errorMessages' => errorMessages,
            'variableSettings' => variableSettings
        };
    }

    /**
    * Private method to get and assign the firstDayOfWeek
    */
    private static Map<String, Object> assignFirstDay() {

        List<Object> variableSettings = new List<Object>();

        //initialize Map with Locales and their Start Days
        Map<String, Integer> localeMap = new Map<String, Integer>();
        localeMap = initLocaleMap();
        Integer firstday;
        String firstdayName;
        List<String> dayNames = new List<String>{
                'Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'
        };

        //Check if Context User is an Integration User and get their Locale
        String contextUserType = UserInfo.getUserType();

        if (contextUserType == 'Analytics Cloud Integration User') {
            String contextUserLocale = UserInfo.getLocale();
            system.debug('This is the Integration User' + contextUserLocale);
            firstday = localeMap.get(contextUserLocale);
            system.debug(firstday);
        }
        //Else just get the current Organizations Locale
        else {
            Organization org = [SELECT DefaultLocaleSidKey FROM Organization];
            String contextOrgLocale = org.DefaultLocaleSidKey;
            system.debug('This is the Org ' + contextOrgLocale);
            firstday = localeMap.get(contextOrgLocale);
            system.debug(firstday);
        }

        if (firstday != null) {
            //Assign Start Day to First_Day_Of_Week variable in variables.json
            variableSettings.add(new Map<string, object>{
                    'name' => 'First_Day_Of_Week',
                    'value' => firstday
            });
            firstdayName = dayNames[firstday];
        } else {
            //If the locale doesnt exist in the map, then set the variable to 0 by default.
            variableSettings.add(new Map<string, object>{
                    'name' => 'First_Day_Of_Week',
                    'value' => 0
            });
            firstdayName = dayNames[0];
        }

        return new Map<String, Object>{
                'success' => true,
                'variableSettings' => variableSettings,
                'messages' => new List<String>{
                        'first day of week to ' + firstdayName + '. '
                },
                'mergeWithPrevious' => true
        };
    }


    @RemoteAction
    global static Map<string, object> objectUsage() {
      List<Map<String, Object>> resultList = new List<Map<String, Object>>();
      resultList.add( new Map<String, Object>{
            'success' => true,
            'messages2d' => new List<Object> {
              new List<String>{'CRM Analytics has detected that your org uses the following:'},
              new List<String> {'CRM Analytics has detected your org does not use the following:'}
            }
          });

      resultList.add(hasCollabForecast());
      resultList.add(hasActivities());
      resultList.add(hasProducts());
    //   resultList.add(hasMinimumDataForEDStory());
      // aggregate results
      Map<string, object> aggResultsSoFar = aggregateResults(resultList);
      // We need to know when to filter field access checks based on the object usage
      Boolean hasProducts = aggResultsSoFar.get('Has_Products') == 'Yes';
      Boolean hasActivities = aggResultsSoFar.get('Has_Activities') == 'Yes';
      Boolean hasCollaborativeForecasting = aggResultsSoFar.get('Has_CollaborativeForecasting') == 'Yes';
      Boolean hasCollaborativeForecastingQuota = aggResultsSoFar.get('Has_CollaborativeForecastingQuota') == 'Yes';
      Boolean hasSplits = false;
    //   Map<String, Object> recipeFieldAccessResults = checkRecipeFieldAccess(hasProducts, hasActivities, hasSplits, hasCollaborativeForecasting, hasCollaborativeForecastingQuota);

    //   resultList.add(recipeFieldAccessResults);
      // aggregate results
      return aggregateResults(resultList);
    }


    @RemoteAction
    global static Map<string, object> fieldAccess() {
        // read it from a variable set in Modifier
        return new Map<String, Object>{
                'success' => true,
                'messagesVariable' => 'DefaultsVisibleMessages'
        };
    }

    @RemoteAction
    global static Map<string, object> configuration() {
        List<Map<String, Object>> resultList = new List<Map<String, Object>>();
        resultList.add(setFiscal());
        resultList.add(assignFirstDay());
        resultList.add(hasRoleHierarchy());

        // aggregate results
        return aggregateResults(resultList);
    }

    @RemoteAction
    global static Map<string, object> checkSplitsAndForecastPeriodConfigurationExt() {
        List<Map<String, Object>> resultList = new List<Map<String, Object>>();
        resultList.add(checkSplitsAndForecastPeriodConfiguration());
        // aggregate results
        return aggregateResults(resultList);
    }

    @RemoteAction
    global static Map<string, object> dataInconsistencies() {
        //return hasRoleHierarchy();
        return hasCustomAddressFieldsEnabled();
    }

}