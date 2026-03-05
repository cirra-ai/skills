global class SDO_Platform_EventsCtrl {
   
    global SDO_Platform_EventsCtrl(){}    
    global SDO_Platform_EventsCtrl(ApexPages.StandardController ctrl){}

    @RemoteAction
    global static List<Object> getPages(){
        return [Select Id, Name, Subtitle__c, Theme__c, Background_URL__c From SDO_Platform_Events_Page__c];
    }
    
    @RemoteAction
    global static SDO_Platform_Events_Page__c getPage(String pageId){
        return [Select Id, Name, Subtitle__c, Theme__c, Background_URL__c, 
                (Select Id, Name, Message__c, Action_Data__c, Action_Type__c 
                 From Platform_Event_Buttons__r) 
                From SDO_Platform_Events_Page__c 
                Where Id = :pageId Limit 1];
    }
    
    @RemoteAction
    global static Object upsertPage(String sPage){
        SDO_Platform_Events_Page__c upsertPage = (SDO_Platform_Events_Page__c)JSON.deserialize(sPage, SDO_Platform_Events_Page__c.class);
        upsert upsertPage;
        return upsertPage;
    }
    
    @RemoteAction
    global static Boolean deletePage(String pageId){
        SDO_Platform_Events_Page__c selectedPage = new SDO_Platform_Events_Page__c(Id = pageId);
        delete selectedPage;
        return true;
    }
    
    @RemoteAction
    global static List<Object> getButtons(String pageId){
        return [Select Id, Name, Message__c, Action_Data__c, Action_Type__c From SDO_Platform_Events_Button__c Where Platform_Events_Page__c = :pageId];
    }
    
    @RemoteAction
    global static List<Object> upsertButtons(String sButtons){
        List<SDO_Platform_Events_Button__c> upsertButtons = (List<SDO_Platform_Events_Button__c>)JSON.deserialize(sButtons, List<SDO_Platform_Events_Button__c>.class);
        upsert upsertButtons;
        return upsertButtons;
    }
    
    @RemoteAction
    global static Boolean deleteButton(String buttonId){
        SDO_Platform_Events_Button__c selectedButton = new SDO_Platform_Events_Button__c(Id = buttonId);
        delete selectedButton;
        return true;
    }
    
    @RemoteAction
    global static Boolean deleteButtons(List<String> buttonIds){
        List<SDO_Platform_Events_Button__c> selectedButtons = new List<SDO_Platform_Events_Button__c>();
        for(String buttonId: buttonIds){
            SDO_Platform_Events_Button__c button = new SDO_Platform_Events_Button__c(Id = buttonId);
            selectedButtons.add(button);
        }
        delete selectedButtons;
        return true;
    }
    
    @RemoteAction
    global static Boolean publishNotification(String message) {
        List<Notification__e> notifications = new List<Notification__e>();
        notifications.add(new Notification__e(Message__c = message));
        try {
            List<Database.SaveResult> results = EventBus.publish(notifications);
            
            // Inspect publishing results
            for (Database.SaveResult result : results) {
                if (!result.isSuccess()) {
                    for (Database.Error error : result.getErrors()) {
                        System.debug('Error returned: ' +
                                     error.getStatusCode() +' - '+
                                     error.getMessage());
                    }
                }
            }
            
            return true;
        } catch (Exception e){
            return false;
        }
    }
}