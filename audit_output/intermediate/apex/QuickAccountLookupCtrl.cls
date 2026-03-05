public with sharing class QuickAccountLookupCtrl {
    @AuraEnabled(cacheable=true)
    public static List<Account> searchAccounts(String searchTerm) {
        if (String.isBlank(searchTerm)) {
            return [
                SELECT Id, Name, Industry, Phone, Website, AnnualRevenue
                FROM Account
                WITH SECURITY_ENFORCED
                ORDER BY Name
                LIMIT 10
            ];
        }
        String key = '%' + String.escapeSingleQuotes(searchTerm) + '%';
        return [
            SELECT Id, Name, Industry, Phone, Website, AnnualRevenue
            FROM Account
            WHERE Name LIKE :key
            WITH SECURITY_ENFORCED
            ORDER BY Name
            LIMIT 50
        ];
    }
}