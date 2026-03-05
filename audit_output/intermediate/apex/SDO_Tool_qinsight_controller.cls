public class SDO_Tool_qinsight_controller {
	@AuraEnabled
    public static String getEmail() {

        String userEmail = '';
        User u = [SELECT Email FROM User where Id =:UserInfo.getUserId()];
		userEmail = u.email;

        return userEmail;
    }
}