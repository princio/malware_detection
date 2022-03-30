## Astea

- Wincollect:
  - installazione ed utilizzo

- Studio Windows environment:
  - Studio utilizzo Domain Controllers:
    - studio delle policy di Windows e loro propagazione
  - Eventi di Windows <=> Audit policies:
    - 60 diverse categorie
    - 440 diversi tipi di eventi:
      - ~1000 contando anche i sotto-eventi
- QRadar:
  - Parsing dei log (processo di normalizzazione):
    - QID
    - Properties extractor
    - Event category
  - Rules:
    - studio di come si definisce una rule
    - studio di come si comporta una rule
  - Offenses:
    - studio di cosa sia un offense
    - studio di da cosa dipende una offense
    - studio di come si debbano gestire le offense
  - Studio offense e rules attuali per diminuire il numero di falsi positivi.


## DNS

- Problema ambiguita' suffixes:
  - differenza tra ICANN e PRIVATE suffix
- Nuovo allenamento delle Neural Networks


## Ancharia

- Incontro con Simone e Lorenzo, ho illustrato un po' il funzionamento di QRadar



### Audit Policies

  - Account Logon:
    - Audit Credential Validation
    - Audit Kerberos Authentication Service
    - Audit Kerberos Service Ticket Operations
    - Audit Other Account Logon Events
  - Account Management
    - Audit Application Group Management
    - Audit Computer Account Management
    - Audit Distribution Group Management
    - Audit Other Account Management Events
    - Audit Security Group Management
    - Audit User Account Management
  - Detailed Tracking:
    - Audit DPAPI Activity
    - Audit PNP activity
    - Audit Process Creation
    - Audit Process Termination
    - Audit RPC Events
    - Audit Token Right Adjusted
  - DS Access:
    - Audit Detailed Directory Service Replication
    - Audit Directory Service Access
    - Audit Directory Service Changes
    - Audit Directory Service Replication
  - Logon/Logoff:
    - Audit Account Lockout
    - Audit User/Device Claims
    - Audit IPsec Extended Mode
    - Audit Group Membership
    - Audit IPsec Main Mode
    - Audit IPsec Quick Mode
    - Audit Logoff
    - Audit Logon
    - Audit Network Policy Server
    - Audit Other Logon/Logoff Events
    - Audit Special Logon
  - Object Access:
    - Audit Application Generated
    - Audit Certification Services
    - Audit Detailed File Share
    - Audit File Share
    - Audit File System
    - Audit Filtering Platform Connection
    - Audit Filtering Platform Packet Drop
    - Audit Handle Manipulation
    - Audit Kernel Object
    - Audit Other Object Access Events
    - Audit Registry
    - Audit Removable Storage
    - Audit SAM
    - Audit Central Access Policy Staging
  - Policy Change:
    - Audit Audit Policy Change
    - Audit Authentication Policy Change
    - Audit Authorization Policy Change
    - Audit Filtering Platform Policy Change
    - Audit MPSSVC Rule-Level Policy Change
    - Audit Other Policy Change Events
  - Privilege Use:
    - Audit Non-Sensitive Privilege Use
    - Audit Sensitive Privilege Use
    - Audit Other Privilege Use Events
    System:
    - Audit IPsec Driver
    - Audit Other System Events
    - Audit Security State Change
    - Audit Security System Extension
    - Audit System Integrity
