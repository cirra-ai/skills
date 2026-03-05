global class DBM25PostInstallScript implements InstallHandler {
    global static final String permSetName = 'Dashboard_Magic_User';

    global void onInstall(InstallContext context) {
        // String permSetName = ''
        PermissionSet permSet = [SELECT Id FROM PermissionSet WHERE Name =: permSetName];
        if (permSet != null) {
            PermissionSetAssignment psa = new PermissionSetAssignment(PermissionSetId = permSet.Id, AssigneeId = context.installerID());
            insert psa;
        }
    }
}