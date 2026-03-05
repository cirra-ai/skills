public class SDO_Platform_EventsNotificationCtrl {
    @AuraEnabled
    public static String getSessionId() {
        return UserInfo.getSessionId();
    }
}