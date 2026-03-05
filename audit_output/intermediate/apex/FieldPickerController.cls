/*
This file is generated and isn't the actual source code for this
managed global class.
This read-only file shows the class's global constructors,
methods, variables, and properties.
To enable code to compile, all methods return null.
*/
global class FieldPickerController {
    global FieldPickerController() {

    }
    @AuraEnabled
    global static List<usf3.FieldPickerController.Member> getObjects(List<String> availableObjectTypes) {
        return null;
    }
    @AuraEnabled
    global static List<usf3.FieldPickerController.Member> getPicklistValues(String objectApiName, String fieldName) {
        return null;
    }
global class Member implements System.Comparable {
    @AuraEnabled
    global Boolean isActive;
    @AuraEnabled
    global Boolean isDefaultValue;
    @AuraEnabled
    global String label;
    @AuraEnabled
    global String value;
    global Member(String value, String label) {

    }
    global Member(String value, String label, Boolean isActive, Boolean isDefaultValue) {

    }
    global Integer compareTo(Object compareTo) {
        return null;
    }
}
}
