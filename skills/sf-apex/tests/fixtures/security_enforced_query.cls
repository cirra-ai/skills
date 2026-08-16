/**
 * @description Selector using the legacy WITH SECURITY_ENFORCED clause.
 * Fixture for version-aware validation: compiles at API <= 66.0, does not
 * compile at API >= 67.0 (clause removed in Summer '26).
 */
public with sharing class SecurityEnforcedQuery {
    /**
     * @description Returns active accounts enforcing FLS via the legacy clause.
     * @return List of accounts
     */
    public static List<Account> getActiveAccounts() {
        try {
            return [
                SELECT Id, Name
                FROM Account
                WHERE IsActive__c = TRUE
                WITH SECURITY_ENFORCED
                LIMIT 200
            ];
        } catch (System.QueryException e) {
            throw new AuraHandledException('Access denied: ' + e.getMessage());
        }
    }
}
