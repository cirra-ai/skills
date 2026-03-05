global class SDO_Service_ResetUserPassword {
    
	@InvocableMethod(label='SDO Service - Reset User Password' description='Resets user passwords based on User ID(s) passed')
    global static List<Boolean> resetUserPassword (List<ResetUserPasswordInput> requests) {
        List<Boolean> results = new List<Boolean>();
        
        for (ResetUserPasswordInput input : requests) {
            System.ResetPasswordResult resetResult = null;
            if (input.userId != null) {
                resetResult = system.resetPassword(input.userId, true);
                results.add(true);
            } 
            
            if (input.listOfUserIds != null) {
                for (String userId : input.listOfUserIds) {
                  resetResult = System.resetPassword(userId, true);
                }
                results.add(true);              
            } 
            
            if (resetResult == null) {
                results.add(false);
            }
        }
        
        return results;
    }
    
    global class ResetUserPasswordInput {
        @invocableVariable(label='ID of the user record' description='User with this ID will have their Salesforce password reset' required=false)
        global String userId;
        
        @invocableVariable(label='List of User IDs' description='Users with an ID in this list will have their Salesforce password reset' required=false)
        global List<String> listOfUserIds;
        
    }
}