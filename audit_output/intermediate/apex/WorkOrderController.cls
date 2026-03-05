public class WorkOrderController {
    @AuraEnabled(cacheable=true)
    public static List<ProductRequiredWrapper> getProductsForWorkType(Id workTypeId) {
        if (String.isEmpty(workTypeId)) {
            return new List<ProductRequiredWrapper>();
        }

        List<ProductRequiredWrapper> resultList = new List<ProductRequiredWrapper>();

        // Fetch related products from ProductRequired
        List<ProductRequired> productRequiredList = [
            SELECT Id, Product2Id, Product2.Name, QuantityRequired
            FROM ProductRequired
            WHERE ParentRecordId = :workTypeId
        ];

        // Get Product2 Ids
        Set<Id> productIds = new Set<Id>();
        for (ProductRequired pr : productRequiredList) {
            if (pr.Product2Id != null) {
                productIds.add(pr.Product2Id);
            }
        }

        // Fetch Unit Price from PricebookEntry
        Map<Id, Decimal> productPriceMap = new Map<Id, Decimal>();
        if (!productIds.isEmpty()) {
            for (PricebookEntry pbe : [
                SELECT Product2Id, UnitPrice
                FROM PricebookEntry
                WHERE Product2Id IN :productIds
                AND IsActive = true
                AND Pricebook2.IsStandard = true
            ]) {
                productPriceMap.put(pbe.Product2Id, pbe.UnitPrice);
            }
        }

        // Build the response
        for (ProductRequired pr : productRequiredList) {
            resultList.add(new ProductRequiredWrapper(
                pr.Id,
                pr.Product2 != null ? pr.Product2.Name : 'N/A',
                pr.QuantityRequired,
                productPriceMap.containsKey(pr.Product2Id) ? productPriceMap.get(pr.Product2Id) : 0
            ));
        }

        return resultList;
    }

	public class ProductRequiredWrapper {
        @AuraEnabled public Id id;
        @AuraEnabled public String productName;
        @AuraEnabled public Decimal quantityRequired;
        @AuraEnabled public Decimal unitPrice;

        public ProductRequiredWrapper(Id id, String productName, Decimal quantityRequired, Decimal unitPrice) {
            this.id = id;
            this.productName = productName;
            this.quantityRequired = quantityRequired;
            this.unitPrice = unitPrice;
        }
    }
}