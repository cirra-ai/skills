public class Sdo_Scom_OM_PrintInvoiceController {
    private final Invoice invoice;
    private final OrderSummary ordersummary;
    private final OrderDeliveryGroupSummary orderdeliverygroupsummary;
    private final List<PaymentLineInvoice> payment;
    private final FulfillmentOrder fulfillmentOrder;
    
    public Sdo_Scom_OM_PrintInvoiceController() {
        invoice = [SELECT Id, Balance, DocumentNumber, DueDate, InvoiceDate, Status,
                   TotalAdjustmentAmount, TotalAmount, TotalAmountWithTax, TotalChargeAmount,
                   TotalTaxAmount, ReferenceEntityId, TotalAdjustmentAmountWithTax,
                   (	SELECT Product2.Name, Product2.Description, Quantity, GrossUnitPrice,
                    	ChargeTaxAmount, Type, UnitPrice, ReferenceEntityItemTypeCode,
                    	AdjustmentAmountWithTax, LineAmount
                    	FROM InvoiceLines
                    	WHERE Type = 'Charge' and Quantity > 0
                   		ORDER BY ReferenceEntityItemTypeCode)
                   FROM Invoice 
                   WHERE Id = :ApexPages.currentPage().getParameters().get('id')];
        ordersummary = [SELECT Id, OrderNumber, OrderedDate, BillingStreet, BillingCity, BillingState,
                        BillingPostalCode, BillingCountry, BillingPhoneNumber
                        FROM OrderSummary
                        WHERE Id = :invoice.ReferenceEntityId];
        orderdeliverygroupsummary = [SELECT Id, OrderDeliveryMethod.Name
                             FROM OrderDeliveryGroupSummary
                             WHERE OrderSummaryId = :ordersummary.Id];
        fulfillmentOrder = [SELECT
                            	Id,
                            	DeliveryMethod.Name
                            FROM FulfillmentOrder
                            WHERE InvoiceId = :invoice.Id];
        payment = [SELECT Payment.Id, Payment.Amount,
                   TYPEOF Payment.PaymentMethod WHEN CardPaymentMethod THEN CardType When DigitalWallet THEN Type END
                   FROM PaymentLineInvoice
                   WHERE InvoiceId = :invoice.Id];
    }
    
    public Invoice getInvoice() {
        return invoice;
    }
    
    public OrderSummary getOrderSummary() {
        return ordersummary;
    }
    
    public OrderDeliveryGroupSummary getOrderDeliveryGroupSummary() {
        return orderdeliverygroupsummary;
    }
    
    public List<PaymentLineInvoice> getPayment() {
        return payment;
    }
    
    public FulfillmentOrder getFulfillmentOrder() {
        return fulfillmentOrder;
    }
    
}