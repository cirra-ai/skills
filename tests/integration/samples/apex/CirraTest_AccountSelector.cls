/**
 * @description Selector class for Account queries.
 *              Centralizes all Account SOQL queries with proper security enforcement.
 * @author      CirraTest
 * @date        2025-01-15
 */
public with sharing class CirraTest_AccountSelector {

    /**
     * @description Select accounts by IDs.
     * @param accountIds Set of Account IDs.
     * @return List of Account records.
     */
    public static List<Account> selectById(Set<Id> accountIds) {
        return [
            SELECT Id, Name, Industry, AnnualRevenue, BillingCity, Rating
            FROM Account
            WHERE Id IN :accountIds
            WITH USER_MODE
        ];
    }

    /**
     * @description Select accounts by IDs with their related Contacts.
     * @param accountIds Set of Account IDs.
     * @return List of Account records with Contacts subquery.
     */
    public static List<Account> selectByIdWithContacts(Set<Id> accountIds) {
        return [
            SELECT Id, Name, Industry,
                   (SELECT Id, FirstName, LastName, Email, Title FROM Contacts)
            FROM Account
            WHERE Id IN :accountIds
            WITH USER_MODE
        ];
    }

    /**
     * @description Select accounts by Industry.
     * @param industry The industry value to filter by.
     * @return List of Account records matching the industry.
     */
    public static List<Account> selectByIndustry(String industry) {
        return [
            SELECT Id, Name, Industry, AnnualRevenue, BillingCity
            FROM Account
            WHERE Industry = :industry
            WITH USER_MODE
            ORDER BY Name ASC
        ];
    }

    /**
     * @description Select active accounts (Rating is not null).
     * @return List of active Account records.
     */
    public static List<Account> selectActive() {
        return [
            SELECT Id, Name, Industry, AnnualRevenue, Rating
            FROM Account
            WHERE Rating != null
            WITH USER_MODE
            ORDER BY AnnualRevenue DESC NULLS LAST
        ];
    }

    /**
     * @description Select accounts by annual revenue range.
     * @param minRevenue Minimum annual revenue.
     * @param maxRevenue Maximum annual revenue.
     * @return List of Account records in the revenue range.
     */
    public static List<Account> selectByRevenueRange(Decimal minRevenue, Decimal maxRevenue) {
        return [
            SELECT Id, Name, Industry, AnnualRevenue
            FROM Account
            WHERE AnnualRevenue >= :minRevenue
              AND AnnualRevenue <= :maxRevenue
            WITH USER_MODE
            ORDER BY AnnualRevenue DESC
        ];
    }

    /**
     * @description Count accounts grouped by Industry.
     * @return List of AggregateResult with Industry and count.
     */
    public static List<AggregateResult> countByIndustry() {
        return [
            SELECT Industry, COUNT(Id) numAccounts
            FROM Account
            WHERE Industry != null
            WITH USER_MODE
            GROUP BY Industry
            ORDER BY COUNT(Id) DESC
        ];
    }
}
