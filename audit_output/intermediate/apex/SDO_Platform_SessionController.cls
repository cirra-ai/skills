public class SDO_Platform_SessionController {
    @AuraEnabled
    public static String getSessionId() {
        return UserInfo.getSessionId();
    }
}