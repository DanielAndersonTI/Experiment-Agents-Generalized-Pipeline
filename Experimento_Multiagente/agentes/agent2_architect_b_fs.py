"""
Agente 2: Microservice Communication Specialist (Arquiteto B) – Few-Shot

Especialista em identificação precisa de interações entre microsserviços.

O Agente 2 produz uma proposta arquitetural INDEPENDENTE a partir dos
requisitos textuais do sistema.

Seu objetivo é gerar uma segunda decomposição arquitetural, com atenção
especial às interações entre serviços, priorizando precisão e evidência
sobre criatividade ou cobertura especulativa.

A arquitetura de outro agente NÃO é fornecida como entrada para B.

A biblioteca Few-Shot contém exemplos abstratos e independentes de domínio
para ensinar padrões generalizáveis de dependência entre capacidades.
"""

from crewai import Agent, Task


# ============================================================================
# Biblioteca de exemplos generalizáveis de inferência de interações
# ============================================================================

INTERACTION_EXAMPLES = """
EXAMPLES OF GENERALIZABLE INTER-SERVICE INTERACTION REASONING

The examples below are NOT templates to copy and do NOT prescribe specific
service names for the target system. Their purpose is to teach general
reasoning patterns for identifying necessary communication between
independent capabilities.

Use them as architectural reasoning examples, not as domain knowledge.

---------------------------------------------------------------------- 
PATTERN 1 — DATA OWNERSHIP DEPENDENCY
----------------------------------------------------------------------

Scenario:
A Customer Profile service owns customer address information.
A Shipping service is responsible for calculating and scheduling shipments.

Requirement:
"Shipments must be scheduled using the customer's delivery address."

Reasoning:
Shipping needs customer address data.
Customer Profile owns that data.
The shipment responsibility cannot be completed with the required data
unless Shipping obtains that information.

Conclusion:
A communication between Shipping and Customer Profile is justified.

General principle:
When service A needs data that is explicitly owned or managed by service B
in order to perform a stated responsibility, the dependency is strong
evidence for an interaction.

---------------------------------------------------------------------- 
PATTERN 2 — ACTION DEPENDENCY
----------------------------------------------------------------------

Scenario:
An Account service manages account registration.
An Identity service performs authentication.

Requirement:
"Users must be authenticated before accessing protected account operations."

Reasoning:
Authentication is performed by Identity.
Account operations depend on successful authentication.

Conclusion:
A communication between Account and Identity is justified.

General principle:
When one service cannot complete a stated operation without an action
performed by another service, the dependency can justify communication.

---------------------------------------------------------------------- 
PATTERN 3 — COMMAND / BUSINESS ACTION
----------------------------------------------------------------------

Scenario:
A Reservation service creates reservations.
A Resource Allocation service reserves physical capacity.

Requirement:
"Creating a reservation must allocate the requested capacity."

Reasoning:
Reservation creation requires an allocation action controlled by the
Resource Allocation capability.

Conclusion:
Reservation -> Resource Allocation is justified.

General principle:
A direct business action performed by one capability on behalf of another
is strong evidence for communication.

---------------------------------------------------------------------- 
PATTERN 4 — BUSINESS WORKFLOW DEPENDENCY
----------------------------------------------------------------------

Scenario:
A Checkout service finalizes purchases.
A Billing service issues invoices.

Requirement:
"After a purchase is finalized, an invoice must be issued."

Reasoning:
The invoice operation depends on purchase completion.

Conclusion:
Checkout -> Billing is justified.

General principle:
When requirements explicitly connect two steps in a business workflow,
the participating services should communicate.

---------------------------------------------------------------------- 
PATTERN 5 — PAYMENT PROCESSING
----------------------------------------------------------------------

Scenario:
An Order service creates orders.
A Payment service processes charges.

Requirement:
"Orders must be paid before they are considered completed."

Reasoning:
Order completion depends on payment processing.

Conclusion:
Order <-> Payment is potentially justified, depending on the described
flow and whether payment status must be returned to Order.

Important:
Do NOT automatically assume bidirectional communication. Infer direction
only when the requirements support it.

General principle:
A workflow dependency justifies communication, but directionality must still
be supported.

---------------------------------------------------------------------- 
PATTERN 6 — INVENTORY / AVAILABILITY
----------------------------------------------------------------------

Scenario:
A Reservation service reserves products.
An Inventory service maintains available quantities.

Requirement:
"Reservations may only be confirmed when sufficient inventory exists."

Reasoning:
Reservation confirmation requires inventory availability information.

Conclusion:
Reservation -> Inventory is justified.

General principle:
Validation against data owned by another capability creates a dependency.

---------------------------------------------------------------------- 
PATTERN 7 — DELIVERY / FULFILLMENT
----------------------------------------------------------------------

Scenario:
An Order service manages finalized orders.
A Logistics service schedules deliveries.

Requirement:
"Delivery scheduling is performed using finalized order information."

Reasoning:
Logistics depends on information controlled by Order.

Conclusion:
Order -> Logistics is justified.

General principle:
If downstream fulfillment explicitly depends on upstream business state,
communication is justified.

---------------------------------------------------------------------- 
PATTERN 8 — NOT JUSTIFIED: SHARED BUSINESS CONTEXT
----------------------------------------------------------------------

Scenario:
A Catalog service manages products.
A Customer service manages customer profiles.

Requirement:
"The system allows customers to view their profiles and administrators
to manage products."

Reasoning:
Both capabilities belong to the same application, but neither requirement
states that Customer needs Catalog data or that Catalog needs Customer data.

Conclusion:
DO NOT create Customer -> Catalog merely because both are business services.

General principle:
Conceptual coexistence is NOT evidence of interaction.

---------------------------------------------------------------------- 
PATTERN 9 — NOT JUSTIFIED: SAME WORKFLOW, NO DEPENDENCY
----------------------------------------------------------------------

Scenario:
A Reporting service produces reports.
A Notification service sends messages.

Requirement:
"The system generates reports and allows users to receive notifications."

Reasoning:
Both capabilities are related to user-facing functionality, but no
requirement states that reports must be sent through Notification.

Conclusion:
DO NOT create Reporting -> Notification unless the requirements connect
the two responsibilities.

General principle:
Participation in the same broad system or user journey is insufficient.

---------------------------------------------------------------------- 
PATTERN 10 — EXPLICIT DATA QUERY
----------------------------------------------------------------------

Scenario:
A Pricing service calculates prices.
A Tax service determines applicable taxes.

Requirement:
"Prices must include the tax calculated according to the customer's region."

Reasoning:
Pricing requires tax information from Tax.

Conclusion:
Pricing -> Tax is justified.

General principle:
An explicit data lookup required to complete a responsibility is strong
interaction evidence.

---------------------------------------------------------------------- 
PATTERN 11 — AUTHORIZATION
----------------------------------------------------------------------

Scenario:
A Document service stores protected documents.
An Access Control service manages permissions.

Requirement:
"Users may retrieve documents only after their permissions have been
validated."

Reasoning:
Document access depends on authorization performed by Access Control.

Conclusion:
Document -> Access Control is justified.

General principle:
Security checks that are explicitly required by a business operation
justify communication.

---------------------------------------------------------------------- 
PATTERN 12 — NOT JUSTIFIED: GENERIC SECURITY ASSUMPTION
----------------------------------------------------------------------

Scenario:
A Product service exists.
An Authentication service exists.

Requirement:
"The system supports user authentication."

Reasoning:
Authentication exists, but the requirement does not state that Product
operations require authentication or authorization.

Conclusion:
DO NOT automatically connect Product -> Authentication unless the
requirements establish that dependency.

General principle:
The mere existence of an authentication capability does not justify
connecting every service to it.

---------------------------------------------------------------------- 
PATTERN 13 — EVENT / STATE CHANGE
----------------------------------------------------------------------

Scenario:
A Subscription service manages subscriptions.
A Notification service sends renewal reminders.

Requirement:
"Customers receive a notification when a subscription is about to expire."

Reasoning:
The expiration state of Subscription triggers a Notification responsibility.

Conclusion:
Subscription -> Notification is justified.

General principle:
A requirement explicitly triggered by a state change supports interaction.

---------------------------------------------------------------------- 
PATTERN 14 — EVENT NOT IMPLIED
----------------------------------------------------------------------

Scenario:
A Purchase service completes purchases.
An Analytics service provides dashboards.

Requirement:
"The system provides purchase history and analytics dashboards."

Reasoning:
Analytics could theoretically consume purchase data, but the requirement
does not explicitly establish a communication mechanism or dependency.

Conclusion:
Do NOT automatically create Purchase -> Analytics.

General principle:
A technically plausible event/data flow is not sufficient without
requirement support.

---------------------------------------------------------------------- 
PATTERN 15 — WORKFLOW COORDINATION
----------------------------------------------------------------------

Scenario:
A Travel Booking service creates bookings.
A Seat Allocation service assigns seats.

Requirement:
"A booking is confirmed only after a seat has been assigned."

Reasoning:
Booking confirmation depends on seat allocation.

Conclusion:
Booking -> Seat Allocation is justified.

General principle:
A prerequisite business operation creates a strong dependency.

---------------------------------------------------------------------- 
PATTERN 16 — RETURNED RESULT / STATUS
----------------------------------------------------------------------

Scenario:
An Order service requests payment processing.
A Payment service returns payment success or failure.

Requirement:
"An order is completed only when payment succeeds."

Reasoning:
Order sends a payment request and needs the result.

Conclusion:
Order <-> Payment may be justified if both request and result exchange
are represented as service communication.

General principle:
Use bidirectional communication only when the information flow actually
requires both directions.

---------------------------------------------------------------------- 
PATTERN 17 — SHARED ENTITY DOES NOT IMPLY COMMUNICATION
----------------------------------------------------------------------

Scenario:
Several services refer to "user" in their responsibilities.

Requirement:
"Users can manage preferences and can place requests."

Reasoning:
The same conceptual entity appears in multiple services, but the
requirements do not establish that the Preference service must communicate
with Request service.

Conclusion:
Do NOT infer an interaction merely because both mention users.

General principle:
Shared vocabulary is not sufficient evidence of dependency.

---------------------------------------------------------------------- 
PATTERN 18 — CROSS-SERVICE VALIDATION
----------------------------------------------------------------------

Scenario:
A Registration service stores accounts.
A Verification service validates submitted identity information.

Requirement:
"Accounts are activated only after identity verification."

Reasoning:
Activation depends on Verification.

Conclusion:
Registration -> Verification is justified.

General principle:
Cross-service validation needed to complete a required operation is a
strong interaction.

---------------------------------------------------------------------- 
PATTERN 19 — OPTIONAL FEATURE IS NOT AUTOMATIC DEPENDENCY
----------------------------------------------------------------------

Scenario:
A Product service manages products.
A Recommendation service suggests products.

Requirement:
"The system may optionally provide product recommendations."

Reasoning:
Recommendations are optional and not necessarily required by product
management.

Conclusion:
Do not infer Product -> Recommendation unless the requirement explicitly
defines the data exchange or dependency.

General principle:
Optional functionality should not create a mandatory architectural
dependency without evidence.

---------------------------------------------------------------------- 
PATTERN 20 — SERVICE-TO-INFRASTRUCTURE
----------------------------------------------------------------------

Scenario:
A service discovery component exists in the architecture.

Requirement:
"Services register and locate each other through service discovery."

Reasoning:
This requirement explicitly establishes the infrastructure dependency.

Conclusion:
Communication with the discovery component is justified.

General principle:
Technical components may be included when the requirements explicitly
require them.

---------------------------------------------------------------------- 
PATTERN 21 — INFRASTRUCTURE NOT REQUIRED
----------------------------------------------------------------------

Scenario:
A system could theoretically use a message broker.

Requirement:
"The system processes orders and updates customers."

Reasoning:
No requirement mentions asynchronous messaging or a broker.

Conclusion:
Do NOT create service -> broker interactions.

General principle:
Never introduce infrastructure communication based only on common
architectural practice.

---------------------------------------------------------------------- 
PATTERN 22 — DATABASE OWNERSHIP
----------------------------------------------------------------------

Scenario:
An Account service owns account data.
A Billing service needs the customer's billing address.

Requirement:
"Billing uses the customer's registered billing address."

Reasoning:
Billing depends on data owned by Account.

Conclusion:
Billing -> Account is justified.

General principle:
Explicit data ownership creates a strong dependency even if the
requirements do not use the word "communicate."

---------------------------------------------------------------------- 
PATTERN 23 — DUPLICATED RESPONSIBILITY
----------------------------------------------------------------------

Scenario:
Two services both appear capable of managing the same resource.

Requirement:
"Only the Account service manages account registration."

Reasoning:
Another service should not be invented as an additional account source
unless the requirements explicitly define it.

Conclusion:
Do not create communication merely to synchronize duplicated,
unsupported responsibilities.

General principle:
First establish ownership; then infer dependencies.

---------------------------------------------------------------------- 
PATTERN 24 — ORCHESTRATOR
----------------------------------------------------------------------

Scenario:
A Workflow service coordinates fulfillment.
Shipping and Billing perform specialized actions.

Requirement:
"The workflow completes billing and shipping before the transaction is
closed."

Reasoning:
Workflow depends on both capabilities.

Conclusion:
Workflow -> Billing and Workflow -> Shipping are justified.

General principle:
A coordinator communicates with downstream services when the workflow
explicitly requires their actions.

---------------------------------------------------------------------- 
PATTERN 25 — NO TRANSITIVE COMMUNICATION
----------------------------------------------------------------------

Scenario:
A -> B is required.
B -> C is required.

Requirement:
A depends on B and B depends on C.

Reasoning:
The fact that A depends on B and B depends on C does NOT automatically
mean A communicates with C.

Conclusion:
Do NOT infer A -> C unless the requirements independently support it.

General principle:
Do not create transitive edges automatically.

---------------------------------------------------------------------- 
PATTERN 26 — NO COMPLETE-MESH ASSUMPTION
----------------------------------------------------------------------

Scenario:
Several services participate in a process.

Requirement:
Each service performs a distinct responsibility and only selected
dependencies are described.

Reasoning:
A process involving five services does not imply that every service talks
to every other service.

Conclusion:
Create only the edges required by the stated responsibilities and flows.

General principle:
Prefer sparse, justified dependency graphs over fully connected graphs.

---------------------------------------------------------------------- 
PATTERN 27 — DOMAIN-DRIVEN DEPENDENCY
----------------------------------------------------------------------

Scenario:
A service owns a bounded context for one business capability.
Another bounded context requires information controlled by the first.

Requirement:
"The Account capability provides the data required by the Compliance
capability to evaluate account status."

Reasoning:
The bounded-context boundary creates a dependency.

Conclusion:
Compliance -> Account is justified.

General principle:
DDD boundaries help identify ownership and dependency, but DDD alone does
not justify communication; the business dependency must also exist.

---------------------------------------------------------------------- 
PATTERN 28 — SEMANTIC RELATION WITHOUT OPERATIONAL DEPENDENCY
----------------------------------------------------------------------

Scenario:
A Search service indexes Products.
A Recommendation service also uses Product concepts.

Requirement:
"Products can be searched and recommendations can be displayed."

Reasoning:
Both use product concepts, but no required dependency between the two
is described.

Conclusion:
Do NOT create Search -> Recommendation merely because they are semantically
related.

General principle:
Semantic similarity is weaker evidence than a required operational flow.

---------------------------------------------------------------------- 
PATTERN 29 — REQUIRED RESULT FEEDBACK
----------------------------------------------------------------------

Scenario:
An Application service submits an application.
An Evaluation service decides whether it is approved.

Requirement:
"An application is accepted only after evaluation approval."

Reasoning:
Application depends on Evaluation's decision.

Conclusion:
Application -> Evaluation, with return information when required by the
workflow, is justified.

General principle:
When a downstream decision determines the upstream business state,
the dependency is strong.

---------------------------------------------------------------------- 
PATTERN 30 — COMMUNICATION THROUGH A USER IS NOT SERVICE COMMUNICATION
----------------------------------------------------------------------

Scenario:
Two independent services are both used by the same user.

Requirement:
"Users can create projects and independently manage notifications."

Reasoning:
The user may interact with both capabilities, but the services themselves
do not necessarily communicate.

Conclusion:
Do NOT create Project -> Notification solely because the same user uses both.

General principle:
Human-mediated interaction is not automatically inter-service
communication.

---------------------------------------------------------------------- 
PATTERN 31 — CUSTOMER -> ORDER DATA DEPENDENCY
----------------------------------------------------------------------

Scenario:
A Customer service owns customer identity and profile data.
An Order service creates orders.

Requirement:
"An order must contain the customer's registered identity."

Reasoning:
Order creation requires customer information controlled by Customer.

Conclusion:
Order -> Customer is justified.

General principle:
A downstream business record depending on information owned by another
service creates an interaction.

---------------------------------------------------------------------- 
PATTERN 32 — ORDER -> PRODUCT VALIDATION
----------------------------------------------------------------------

Scenario:
An Order service creates orders.
A Product service manages product information.

Requirement:
"An order can contain only products that currently exist in the catalog."

Reasoning:
Order validation requires information from Product.

Conclusion:
Order -> Product is justified.

General principle:
Reference-data validation creates a dependency.

---------------------------------------------------------------------- 
PATTERN 33 — CART -> PRODUCT AVAILABILITY
----------------------------------------------------------------------

Scenario:
A Cart service manages shopping carts.
A Product or Inventory service manages available items.

Requirement:
"Items can only be added to the cart when they are available."

Reasoning:
Cart needs availability information.

Conclusion:
Cart -> Product/Inventory is justified if that service owns the relevant
availability information.

General principle:
Precondition checks create communication.

---------------------------------------------------------------------- 
PATTERN 34 — CART -> CUSTOMER NOT AUTOMATIC
----------------------------------------------------------------------

Scenario:
Cart and Customer services both exist.

Requirement:
"Customers may maintain a shopping cart."

Reasoning:
The requirement does not necessarily state that Cart must retrieve
Customer information.

Conclusion:
Do NOT create Cart -> Customer solely because carts belong to customers.

General principle:
Ownership of a business concept does not automatically establish an
operational dependency.

---------------------------------------------------------------------- 
PATTERN 35 — ORDER -> PAYMENT
----------------------------------------------------------------------

Scenario:
Order Service manages completed orders.
Payment Service processes payment.

Requirement:
"An order becomes confirmed only after successful payment."

Reasoning:
Order state depends on Payment result.

Conclusion:
Order -> Payment is justified.

---------------------------------------------------------------------- 
PATTERN 36 — ORDER -> DELIVERY
----------------------------------------------------------------------

Scenario:
Order Service manages confirmed orders.
Delivery Service schedules shipments.

Requirement:
"Confirmed orders are sent for delivery."

Reasoning:
Delivery needs information about confirmed orders.

Conclusion:
Delivery -> Order or Order -> Delivery according to the information flow
specified in the requirements.

General principle:
Determine direction from who needs whose information or action.

---------------------------------------------------------------------- 
PATTERN 37 — DELIVERY -> CUSTOMER
----------------------------------------------------------------------

Scenario:
Delivery Service schedules delivery.
Customer Service maintains delivery addresses.

Requirement:
"Deliveries use the customer's registered delivery address."

Reasoning:
Delivery requires address information owned by Customer.

Conclusion:
Delivery -> Customer is justified.

---------------------------------------------------------------------- 
PATTERN 38 — AUTHENTICATION DOES NOT MEAN UNIVERSAL COUPLING
----------------------------------------------------------------------

Scenario:
Authentication service exists alongside several business services.

Requirement:
"Users can authenticate."

Reasoning:
Authentication capability exists, but no service-specific dependency is
stated.

Conclusion:
Do NOT connect every business service to Authentication automatically.

General principle:
A platform capability becomes an interaction only when a requirement
establishes its use by another service.

---------------------------------------------------------------------- 
PATTERN 39 — AUTHORIZATION REQUIRED FOR ONE OPERATION
----------------------------------------------------------------------

Scenario:
A sensitive Resource service requires permission verification.

Requirement:
"Only authorized users can modify the resource."

Reasoning:
Modification depends on authorization.

Conclusion:
Resource -> Authorization is justified.

Important:
This does NOT imply that every unrelated service must communicate with
Authorization.

---------------------------------------------------------------------- 
PATTERN 40 — AUDIT NOT AUTOMATIC
----------------------------------------------------------------------

Scenario:
An Audit service exists.

Requirement:
"The system stores audit records for administrative changes."

Reasoning:
Only responsibilities involving administrative changes are clearly
connected to Audit.

Conclusion:
Connect the services whose required operations generate those audit
records. Do NOT connect every service automatically.

General principle:
Cross-cutting services should only receive interactions supported by
requirements.

---------------------------------------------------------------------- 
PATTERN 41 — NOTIFICATION AFTER BUSINESS EVENT
----------------------------------------------------------------------

Scenario:
A Registration service creates registrations.
A Notification service sends confirmation messages.

Requirement:
"After registration, the user receives a confirmation message."

Reasoning:
Registration completion directly triggers notification.

Conclusion:
Registration -> Notification is justified.

---------------------------------------------------------------------- 
PATTERN 42 — NOTIFICATION WITHOUT TRIGGER
----------------------------------------------------------------------

Scenario:
Notification service exists.

Requirement:
"The system supports email notifications."

Reasoning:
The existence of notification functionality alone does not establish
which services must invoke it.

Conclusion:
Do NOT connect every service to Notification without a specific trigger.

---------------------------------------------------------------------- 
PATTERN 43 — REPORTING DEPENDS ON SOURCE DATA
----------------------------------------------------------------------

Scenario:
Reporting service generates a report from data owned by another service.

Requirement:
"Reports display the transaction history maintained by Transaction Service."

Reasoning:
Reporting requires transaction information.

Conclusion:
Reporting -> Transaction is justified.

---------------------------------------------------------------------- 
PATTERN 44 — REPORTING NOT NECESSARILY CONNECTED TO EVERYTHING
----------------------------------------------------------------------

Scenario:
Reporting and multiple domain services exist.

Requirement:
"The system provides reporting."

No requirement specifies which data sources are needed.

Reasoning:
It is impossible to justify arbitrary connections solely from the existence
of reporting.

Conclusion:
Do NOT create a broad reporting mesh without evidence.

---------------------------------------------------------------------- 
PATTERN 45 — CONFIGURATION SERVICE
----------------------------------------------------------------------

Scenario:
Configuration Service manages application configuration.

Requirement:
"Services retrieve their configuration from the centralized configuration
service."

Reasoning:
The dependency is explicitly required.

Conclusion:
The specified services -> Configuration dependency is justified.

---------------------------------------------------------------------- 
PATTERN 46 — CONFIGURATION NOT AUTOMATICALLY USED BY EVERY SERVICE
----------------------------------------------------------------------

Scenario:
Configuration Service exists.

Requirement:
"The system centralizes configuration for selected applications."

Reasoning:
Only the applications covered by the requirement have the dependency.

Conclusion:
Do NOT connect every service automatically.

---------------------------------------------------------------------- 
PATTERN 47 — SERVICE DISCOVERY
----------------------------------------------------------------------

Scenario:
Discovery Service maintains service registration.

Requirement:
"Services register themselves with the discovery service."

Conclusion:
Service -> Discovery is justified.

---------------------------------------------------------------------- 
PATTERN 48 — DISCOVERY DOES NOT IMPLY BUSINESS INTERACTION
----------------------------------------------------------------------

Scenario:
Two business services communicate through a discovered endpoint.

Requirement:
"The services use discovery to locate endpoints."

Reasoning:
Discovery is an infrastructure mechanism, not necessarily a business
interaction between all services and all other services.

Conclusion:
Do not infer additional business edges from the existence of discovery.

---------------------------------------------------------------------- 
PATTERN 49 — API GATEWAY ROUTING
----------------------------------------------------------------------

Scenario:
API Gateway receives external requests.

Requirement:
"The gateway routes requests to Account and Order capabilities."

Conclusion:
Gateway -> Account and Gateway -> Order are justified.

---------------------------------------------------------------------- 
PATTERN 50 — GATEWAY AS INTERNAL BUS
----------------------------------------------------------------------

Scenario:
A gateway exists.

Requirement:
"The gateway is the external entry point for clients."

Reasoning:
Nothing establishes that internal services call through the gateway.

Conclusion:
Do NOT create internal-service -> Gateway interactions automatically.

General principle:
Role determines justified communication.

---------------------------------------------------------------------- 
PATTERN 51 — ADMINISTRATION SERVICE
----------------------------------------------------------------------

Scenario:
Administration service controls operational functions.

Requirement:
"Administrators can restart and manage selected applications."

Reasoning:
The affected applications have an operational dependency with
Administration.

Conclusion:
Include only the interactions explicitly supported by the requirement.

---------------------------------------------------------------------- 
PATTERN 52 — MONITORING SERVICE
----------------------------------------------------------------------

Scenario:
Monitoring service observes application health.

Requirement:
"The monitoring service checks the health of deployed applications."

Conclusion:
Monitoring -> monitored services is justified.

---------------------------------------------------------------------- 
PATTERN 53 — MONITORING DOES NOT MEAN BUSINESS DEPENDENCY
----------------------------------------------------------------------

Scenario:
A business service is monitored.

Reasoning:
The monitoring relationship is operational and does not imply that the
business service depends on Monitoring to perform its business function.

Conclusion:
Do not infer business workflow interactions from monitoring alone.

---------------------------------------------------------------------- 
PATTERN 54 — STATUS CHECK
----------------------------------------------------------------------

Scenario:
Service A cannot proceed until Service B reports a specific status.

Requirement:
"Processing continues only when the resource is available."

Reasoning:
The availability status controlled by B is required.

Conclusion:
A -> B is justified.

---------------------------------------------------------------------- 
PATTERN 55 — STATUS NOT REQUIRED
----------------------------------------------------------------------

Scenario:
Two services expose status information.

Requirement:
Both services support status queries independently.

Reasoning:
No operation requires one service to consult the other's status.

Conclusion:
Do NOT create the interaction merely because status exists.

---------------------------------------------------------------------- 
PATTERN 56 — AGGREGATION
----------------------------------------------------------------------

Scenario:
Dashboard service aggregates information from multiple source services.

Requirement:
"The dashboard displays account status and transaction history."

Reasoning:
Dashboard depends on both required sources.

Conclusion:
Dashboard -> Account and Dashboard -> Transaction are justified.

General principle:
Aggregation is interaction when the requirements identify the required
sources.

---------------------------------------------------------------------- 
PATTERN 57 — AGGREGATION WITHOUT DEFINED SOURCE
----------------------------------------------------------------------

Scenario:
Dashboard service exists.

Requirement:
"The system provides analytics."

Reasoning:
No specific source dependency is defined.

Conclusion:
Do NOT invent a complete set of source-service interactions.

---------------------------------------------------------------------- 
PATTERN 58 — CROSS-SERVICE SEARCH
----------------------------------------------------------------------

Scenario:
Search service must search data owned by another capability.

Requirement:
"Users can search registered appointments by veterinarian name."

Reasoning:
Search needs appointment and veterinarian data according to the actual
ownership defined by the architecture.

Conclusion:
Include only the dependency supported by those responsibilities.

---------------------------------------------------------------------- 
PATTERN 59 — SHARED READ MODEL NOT ASSUMED
----------------------------------------------------------------------

Scenario:
Two services could both theoretically query the same data.

Requirement:
No shared read model or data dependency is stated.

Conclusion:
Do NOT create an interaction merely because both could access the same
information.

---------------------------------------------------------------------- 
PATTERN 60 — EXPLICIT DEPENDENCY WITHOUT WORD "COMMUNICATE"
----------------------------------------------------------------------

Requirement:
"A visit can only be registered for an existing pet."

Scenario:
Pet information is owned by Pet-related capability.

Reasoning:
Visit registration requires validating the referenced pet.

Conclusion:
The Visit capability depends on the Pet capability.

General principle:
Requirements often encode interaction through business constraints rather
than explicit communication terminology.

---------------------------------------------------------------------- 
PATTERN 61 — EXISTENCE CONSTRAINT
----------------------------------------------------------------------

Scenario:
A child entity can exist only when a parent entity exists.

Requirement:
"An appointment can only be scheduled for a registered customer."

Conclusion:
If customer ownership resides in another service, the scheduling service
depends on the customer service.

---------------------------------------------------------------------- 
PATTERN 62 — NO EXISTENCE CONSTRAINT
----------------------------------------------------------------------

Scenario:
Two services refer to related records.

Requirement:
"The system stores customers and reports independently."

No requirement states that report generation requires customer data.

Conclusion:
Do NOT infer the interaction.

---------------------------------------------------------------------- 
PATTERN 63 — UPDATE PROPAGATION EXPLICITLY REQUIRED
----------------------------------------------------------------------

Scenario:
A source service changes information.
Another service maintains a derived representation.

Requirement:
"Whenever the source information changes, the derived representation must
be updated."

Conclusion:
Include the interaction between source and derived-data service.

---------------------------------------------------------------------- 
PATTERN 64 — DERIVED DATA NOT EXPLICITLY LINKED
----------------------------------------------------------------------

Scenario:
Two services represent related information.

Requirement:
No statement requires synchronization or propagation.

Conclusion:
Do NOT infer synchronization communication.

---------------------------------------------------------------------- 
PATTERN 65 — BUSINESS RULE VALIDATION
----------------------------------------------------------------------

Scenario:
A service performs an operation subject to a rule controlled by another
capability.

Requirement:
"An operation is permitted only when the account is in good standing."

Reasoning:
If account status is owned by another service, the operation depends on
that service's information.

Conclusion:
Include the dependency.

---------------------------------------------------------------------- 
PATTERN 66 — GENERIC BUSINESS KNOWLEDGE IS NOT EVIDENCE
----------------------------------------------------------------------

Scenario:
In many real systems, Service A normally calls Service B.

Target requirements do not mention the dependency.

Conclusion:
Do NOT add A -> B.

General principle:
General industry conventions cannot replace target-system evidence.

---------------------------------------------------------------------- 
PATTERN 67 — MULTIPLE VALID DEPENDENCIES
----------------------------------------------------------------------

Scenario:
A service requires:
- customer identity;
- product availability;
- payment authorization.

These are owned by three different services.

Conclusion:
All three interactions may be justified if the requirements make all
three dependencies necessary.

General principle:
Do not artificially restrict a service to one communication when several
dependencies are genuinely required.

---------------------------------------------------------------------- 
PATTERN 68 — ONE REQUIREMENT, MULTIPLE INTERACTIONS
----------------------------------------------------------------------

Requirement:
"To complete a booking, the system must verify customer eligibility,
reserve capacity, and process payment."

Reasoning:
Three distinct capabilities participate in completing the responsibility.

Conclusion:
Recover each directly necessary interaction rather than treating the
entire requirement as one generic connection.

---------------------------------------------------------------------- 
PATTERN 69 — MULTIPLE SERVICES, ONE ACTOR
----------------------------------------------------------------------

Scenario:
A user performs actions across three services.

Reasoning:
The same human actor does not imply communication among the services.

Conclusion:
Only requirement-supported service dependencies should be included.

---------------------------------------------------------------------- 
PATTERN 70 — SAME DATABASE DOES NOT EQUAL SERVICE COMMUNICATION
----------------------------------------------------------------------

Scenario:
Two services may access information from the same persistence layer.

Requirement:
No service-to-service dependency is described.

Conclusion:
Do NOT infer direct service communication from shared persistence.

General principle:
Deployment or storage assumptions are not interaction evidence unless
specified.

---------------------------------------------------------------------- 
PATTERN 71 — SERVICE OWNERSHIP
----------------------------------------------------------------------

Scenario:
Service A owns resource X.
Service B must change resource X.

Requirement:
"Changes to resource X are performed by Service A."

Conclusion:
B must interact with A if B's responsibility requires that modification.

---------------------------------------------------------------------- 
PATTERN 72 — OWNERSHIP WITHOUT ACCESS
----------------------------------------------------------------------

Scenario:
Service A owns customer data.
Service B also deals with customer-related functionality.

Requirement:
B has no stated need for A's data or actions.

Conclusion:
Do NOT connect B -> A solely because A owns customer data.

---------------------------------------------------------------------- 
PATTERN 73 — PREREQUISITE OPERATION
----------------------------------------------------------------------

Scenario:
Operation A is permitted only after Operation B succeeds.

Conclusion:
A depends on B.

General principle:
Prerequisite operations are strong interaction evidence.

---------------------------------------------------------------------- 
PATTERN 74 — INDEPENDENT OPERATIONS
----------------------------------------------------------------------

Scenario:
Operation A and Operation B are both available to users.

Requirement:
No dependency between them.

Conclusion:
Do NOT create A -> B.

---------------------------------------------------------------------- 
PATTERN 75 — FAILURE INFORMATION
----------------------------------------------------------------------

Scenario:
Service B performs a required operation.
Service A must react when B fails.

Requirement:
"A cannot be completed if the operation performed by B fails."

Conclusion:
A depends on B and its result.

---------------------------------------------------------------------- 
PATTERN 76 — SUCCESS INFORMATION
----------------------------------------------------------------------

Scenario:
Service B produces a required success status.

Requirement:
"A proceeds only after B reports success."

Conclusion:
A -> B is justified.

---------------------------------------------------------------------- 
PATTERN 77 — ERROR HANDLING DOES NOT CREATE EXTRA EDGES
----------------------------------------------------------------------

Scenario:
A calls B.

Requirement:
"B may fail and A handles that failure."

Conclusion:
This is still the same A -> B dependency.
Do not create additional arbitrary services or edges for error handling.

---------------------------------------------------------------------- 
PATTERN 78 — RETRY DOES NOT CREATE NEW SERVICE DEPENDENCY
----------------------------------------------------------------------

Scenario:
A retries a call to B when necessary.

Conclusion:
Retry behavior does not create A -> C or any additional interaction unless
another capability is explicitly involved.

---------------------------------------------------------------------- 
PATTERN 79 — AUDIT TRAIL EXPLICITLY REQUIRED
----------------------------------------------------------------------

Scenario:
Administrative operations must produce audit records.

Requirement:
"Administrative changes are recorded by the audit capability."

Conclusion:
Those administrative operations -> Audit is justified.

---------------------------------------------------------------------- 
PATTERN 80 — AUDIT ASSUMPTION NOT ENOUGH
----------------------------------------------------------------------

Scenario:
Audit capability exists.

Requirement:
No business or operational action is stated as being audited.

Conclusion:
Do NOT connect all services to Audit automatically.

---------------------------------------------------------------------- 
PATTERN 81 — NOTIFICATION CHANNEL DOES NOT DETERMINE BUSINESS DEPENDENCY
----------------------------------------------------------------------

Scenario:
An email service sends messages.

Requirement:
A specific business service must notify users after a specific event.

Conclusion:
The business service may depend on Notification.

Do not connect unrelated services just because they could send email.

---------------------------------------------------------------------- 
PATTERN 82 — EVENT BUS NOT AUTOMATIC
----------------------------------------------------------------------

Scenario:
An event bus exists in a possible architecture.

Requirement:
No requirement states that events are used between services.

Conclusion:
Do NOT introduce service -> Event Bus interactions.

---------------------------------------------------------------------- 
PATTERN 83 — EXPLICIT EVENT PUBLICATION
----------------------------------------------------------------------

Scenario:
A business service publishes an event that another service consumes.

Requirement:
"When X occurs, Y receives the event."

Conclusion:
The event-producing and event-consuming services are interaction-related.

---------------------------------------------------------------------- 
PATTERN 84 — EVENT CONSUMPTION NOT IMPLIED
----------------------------------------------------------------------

Scenario:
A service could potentially benefit from another service's events.

Requirement:
No event dependency is specified.

Conclusion:
Do NOT infer the subscription.

---------------------------------------------------------------------- 
PATTERN 85 — DATA TRANSFORMATION DEPENDENCY
----------------------------------------------------------------------

Scenario:
Service A produces data required by B in transformed form.

Requirement:
"B uses the information generated by A to complete its responsibility."

Conclusion:
B depends on A.

---------------------------------------------------------------------- 
PATTERN 86 — SAME DATA DOMAIN, DIFFERENT PURPOSE
----------------------------------------------------------------------

Scenario:
A and B both describe the same business concept differently.

Requirement:
No exchange between them is specified.

Conclusion:
Do NOT connect them merely because their data concerns the same domain.

---------------------------------------------------------------------- 
PATTERN 87 — MULTI-STEP VALIDATION
----------------------------------------------------------------------

Scenario:
A requires validation by B and then confirmation by C.

Conclusion:
A -> B and A -> C may both be justified if both operations are necessary.

Do not replace them with an arbitrary A -> B -> C chain unless the
requirements establish that sequence.

---------------------------------------------------------------------- 
PATTERN 88 — SEQUENTIAL DEPENDENCY
----------------------------------------------------------------------

Scenario:
A calls B.
B returns a value that A passes to C.

Requirement:
A's responsibility requires B's result, then C's action.

Conclusion:
A -> B and A -> C may both be required.

Do NOT infer only B -> C if A remains the orchestrating capability.

---------------------------------------------------------------------- 
PATTERN 89 — RESPONSIBILITY PRESERVATION
----------------------------------------------------------------------

Scenario:
Architecture A contains several services.

The role of Agent 2 is to identify communication only.

Conclusion:
Do not change service responsibilities while analyzing interactions.

---------------------------------------------------------------------- 
PATTERN 90 — FINAL GENERAL DECISION
----------------------------------------------------------------------

For every candidate interaction A -> B, ask:

1. Does A require information from B?
2. Does A require an action from B?
3. Does A require validation from B?
4. Does A require a result from B?
5. Does the stated business workflow require A and B to cooperate?
6. Is the dependency necessary to perform a responsibility?

If YES with strong evidence:
INCLUDE.

If the relationship is only:
- plausible;
- conventional;
- convenient;
- conceptually related;
- transitive;
- optional;
- technically possible;
- based only on generic architecture knowledge;

EXCLUDE.

If evidence is insufficient:
EXCLUDE.

The objective is not maximum connectivity.

The objective is the most accurate interaction graph justified by the
requirements.
"""


# ============================================================================
# Criação do agente
# ============================================================================

def criar_agente2(llm):
    agente = Agent(
        role="Microservice Communication Specialist",
        goal="""
        Produce an independent microservice architecture from the textual
        requirements, with particular attention to identifying justified
        inter-service communications.

        Architecture B is an independent alternative proposal.

        Do NOT rely on another architecture, reference implementation,
        predefined service list, benchmark structure, or target-specific
        decomposition.

        Identify business capabilities from the requirements and organize them
        into appropriate services using Domain-Driven Design or equivalent
        architectural reasoning.

        For each service:
        - identify its responsibilities from the requirements;
        - identify justified communications with other services;
        - distinguish necessary dependencies from merely plausible
          relationships.

        Prioritize precision and requirement evidence over creativity,
        architectural convention, or speculative coverage.

        The purpose of B is to provide an independent architectural perspective
        that can later be compared and consolidated with another proposal.
        """,

        backstory=f"""
        You are a senior software architect specialized in microservice
        decomposition, inter-service communication, Domain-Driven Design,
        bounded contexts, dependency analysis, and requirements-driven
        architecture.

        You independently analyze systems from their textual requirements.

        You do NOT receive another architecture as a reference and must not
        assume that another architect has already identified the correct
        services.

        Your reasoning should identify:

        - distinct business capabilities;
        - cohesive service boundaries;
        - ownership of business data;
        - dependencies between capabilities;
        - required business actions;
        - workflow dependencies;
        - validation dependencies;
        - result and status dependencies;
        - justified infrastructure dependencies when explicitly required.

        For communication inference, distinguish carefully between:

        - explicit requirement evidence;
        - strong functional dependency;
        - reasonable but optional architectural possibility;
        - generic software architecture convention;
        - semantic or conceptual similarity.

        Only the first two provide sufficient justification for an interaction.

        When evidence is insufficient, do not create an interaction merely to
        make the architecture appear more complete.

        Use DDD or equivalent reasoning to identify ownership and bounded
        responsibilities, but do not treat DDD concepts themselves as evidence
        that two services must communicate.

        The architectural reasoning library below contains generic examples of
        interaction patterns across multiple domains. These examples are
        intended to teach reusable reasoning patterns, not domain-specific
        solutions.

        Do not copy their service names, business domains, or structures.

        Apply the underlying reasoning patterns to the CURRENT SYSTEM
        REQUIREMENTS.

        ARCHITECTURAL REASONING REFERENCE LIBRARY:

        {INTERACTION_EXAMPLES}
        """,

        llm=llm,
        verbose=True,
        memory=False,
    )

    return agente


# ============================================================================
# Task
# ============================================================================

def criar_task_arquitetura_alternativa(agente):
    task = Task(
        description=f"""
        You will receive:

        1. A generic Few-Shot reasoning library;
        2. The textual requirements of the target system.

        IMPORTANT:

        You will NOT receive Architecture A.

        You must produce an independent architectural proposal.

        ======================================================================
        GENERIC FEW-SHOT REASONING LIBRARY
        ======================================================================

        {INTERACTION_EXAMPLES}

        These examples teach reusable architectural reasoning patterns.

        Do not copy their service names, domain concepts, architectures, or
        interactions into the target system unless independently justified by
        the target requirements.

        ======================================================================
        SYSTEM REQUIREMENTS
        ======================================================================

        {{requirements}}

        ======================================================================
        OBJECTIVE
        ======================================================================

        Produce an INDEPENDENT microservice architecture for the system.

        Your architecture must identify:

        1. Distinct business capabilities;
        2. Appropriate microservices;
        3. Responsibilities of each microservice;
        4. Justified communications between microservices.

        The objective is not to maximize the number of services or
        interactions.

        The objective is to produce the most accurate architecture supported
        by the requirements.

        Prioritize precision over creativity.

        ======================================================================
        SERVICE IDENTIFICATION
        ======================================================================

        Identify service boundaries using:

        - distinct business capabilities;
        - cohesive responsibilities;
        - bounded contexts or equivalent decomposition principles;
        - ownership of business data;
        - functional responsibilities explicitly described in the requirements.

        Do not introduce services merely because they are common in
        microservice architectures.

        Do not introduce infrastructure or technical services unless they are
        explicitly required.

        ======================================================================
        INTERACTION IDENTIFICATION
        ======================================================================

        For each possible interaction A -> B, evaluate:

        1. DATA DEPENDENCY
           Does A require data that B owns, manages, or provides?

        2. ACTION DEPENDENCY
           Does A require B to perform an action?

        3. VALIDATION DEPENDENCY
           Does A require B to validate information before completing a
           required responsibility?

        4. WORKFLOW DEPENDENCY
           Does a stated business workflow require A and B to cooperate?

        5. RESULT DEPENDENCY
           Does A require a result, state, status, or decision controlled by B?

        6. NECESSITY
           Is the communication actually necessary for a responsibility
           described by the requirements?

        7. REQUIREMENT EVIDENCE
           Can the interaction be directly or strongly traced to the
           requirements?

        ======================================================================
        DECISION POLICY
        ======================================================================

        INCLUDE an interaction when:

        - it is explicitly required; OR
        - it is strongly and necessarily implied by a functional dependency.

        EXCLUDE an interaction when it is:

        - merely plausible;
        - conventional;
        - optional;
        - technically possible;
        - conceptually related;
        - based only on shared vocabulary;
        - based only on a shared user or actor;
        - transitive without independent evidence;
        - based only on general software architecture knowledge;
        - introduced only to make the architecture appear more complete.

        When uncertainty remains and strong evidence is absent,
        DO NOT ADD THE INTERACTION.

        Do not infer bidirectional communication unless both directions are
        independently supported.

        Do not infer A -> C merely because A -> B and B -> C exist.

        Do not assume a complete communication mesh.

        ======================================================================
        GENERALIZATION REQUIREMENT
        ======================================================================

        The reasoning must generalize to unseen systems and domains.

        Do not assume the target system belongs to e-commerce, healthcare,
        finance, travel, logistics, education, or any other specific domain.

        Transfer the reasoning patterns from the Few-Shot examples, not their
        domain structures.

        ======================================================================
        OUTPUT FORMAT
        ======================================================================

        Your output MUST be exactly:

        Microservice,Responsibilities,Communicates With
        Service Name,responsibility1;responsibility2;responsibility3,Service1;Service2;Service3

        Rules:

        - One row per microservice identified.
        - Separate responsibilities with semicolons (;).
        - Separate communicating services with semicolons (;).
        - Do NOT use markdown.
        - Do NOT include explanations.
        - Do NOT include section titles.
        - Do NOT include comments.
        - Do NOT include a decision section.
        - Do NOT mention the Few-Shot examples.
        - Do NOT copy example service names unless independently justified.
        - Include only services justified by the current requirements.
        - Include only interactions justified by the current requirements.
        - Use names that naturally represent the identified business
          capabilities.
        - Keep the decomposition coherent and internally consistent.

        Produce the final CSV now.
        """,

        expected_output=(
            "An independent CSV microservice architecture derived from the "
            "target requirements, including justified services, responsibilities, "
            "and inter-service communications."
        ),

        agent=agente,
    )

    return task