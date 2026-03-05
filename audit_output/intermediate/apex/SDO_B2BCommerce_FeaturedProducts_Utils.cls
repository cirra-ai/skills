public with sharing class SDO_B2BCommerce_FeaturedProducts_Utils {
    
    public static Boolean checkIsAccessible(String obj, String[] fieldsToCheck) {

        Boolean hasAccess = true;
 
        SObjectType objType = Schema.getGlobalDescribe().get(obj);
        Map<String,Schema.SObjectField> m = objType.getDescribe().fields.getMap();

        for (String fieldToCheck : fieldsToCheck) {
            // Check if the user has access to view field
            if (!m.get(fieldToCheck).getDescribe().isAccessible()) {
                hasAccess = false;
                break;
            }
        }

        return hasAccess;
    }

    // public static Boolean checkIsUpdateable(String obj, String[] fieldsToCheck) {

    //     Boolean hasAccess = true;
 
    //     SObjectType objType = Schema.getGlobalDescribe().get(obj);
    //     Map<String,Schema.SObjectField> m = objType.getDescribe().fields.getMap();

    //     for (String fieldToCheck : fieldsToCheck) {
    //         // Check if the user has access to view field
    //         if (!m.get(fieldToCheck).getDescribe().isUpdateable()) {

    //             System.debug(fieldToCheck + ' is not updateable');

    //             hasAccess = false;
    //             break;
    //         }
    //     }

    //     return hasAccess;
    // }

    // public static Boolean checkIsCreateable(String obj, String[] fieldsToCheck) {

    //     Boolean hasAccess = true;
 
    //     SObjectType objType = Schema.getGlobalDescribe().get(obj);
    //     Map<String,Schema.SObjectField> m = objType.getDescribe().fields.getMap();

    //     for (String fieldToCheck : fieldsToCheck) {
    //         // Check if the user has access to view field
    //         if (!m.get(fieldToCheck).getDescribe().isCreateable()) {

    //             System.debug(fieldToCheck + ' is not createable');

    //             hasAccess = false;
    //             break;
    //         }
    //     }

    //     return hasAccess;
    // }

    // public static Boolean checkObjectIsDeletable(String obj) {

    //     Boolean hasAccess = true;
 
    //     SObjectType objType = Schema.getGlobalDescribe().get(obj);
        
    //     if (!objType.getDescribe().isDeletable()) {
    //         hasAccess = false;
    //     }

    //     return hasAccess;
    // }
    
}