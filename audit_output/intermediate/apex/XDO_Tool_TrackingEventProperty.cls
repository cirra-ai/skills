public with sharing class XDO_Tool_TrackingEventProperty //NOPMD
{
    @AuraEnabled
    @InvocableVariable(Label='Name' Description='Property name to capture for the event. Snake case.' Required=true)
    public String name;

    @AuraEnabled
    @InvocableVariable(Label='Value' Description='Property value to capture for the event.' Required=true)
    public String value;

    public XDO_Tool_TrackingEventProperty() {
    }

    public XDO_Tool_TrackingEventProperty(String name, String value) {
        this.name = name;
        this.value = value;
    }
}