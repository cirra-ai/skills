/**
 * @description Util methods for B2B commerce on Lightning Samples
 *
 * @see SDO_SCOM_B2B_Product_Compare_Utils
 */
public with sharing class SDO_SCOM_B2B_Product_Compare_Utils {
    private static Map<String, String> communityIdToWebStoreIdCache = new Map<String, String>();
    private static Map<String, ConnectApi.CartItemSortOrder> sortOrderCache = new Map<String, ConnectApi.CartItemSortOrder>();

    public static String resolveCommunityIdToWebstoreId(String communityId) {
        if (communityIdToWebStoreIdCache.containsKey(communityId)) {
        return communityIdToWebStoreIdCache.get(communityId);
        } else {
        String webStoreId = [
            SELECT WebStoreId
            FROM WebStoreNetwork
            WHERE NetworkId = :communityId
            WITH SECURITY_ENFORCED
            LIMIT 1
        ]
        .WebStoreId;
        communityIdToWebStoreIdCache.put(communityId, webStoreId);
        return webStoreId;
        }
    }

    public static ConnectApi.CartItemSortOrder resolveSortParam(
        String sortParam
    ) {
        if (sortOrderCache.isEmpty()) {
            for (
            ConnectApi.CartItemSortOrder sortOrder : ConnectApi.CartItemSortOrder.values()
            ) {
                sortOrderCache.put(sortOrder.name(), sortOrder);
            }
        }
        return sortOrderCache.get(sortParam);
    }
}