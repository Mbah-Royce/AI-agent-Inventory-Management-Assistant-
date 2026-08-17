How Race Condition was prevented.

Optimistic concurrency control was used at the technqiue to determine race condition.
A version attribute for each role was used to monitor row change in the course
of a agent still in process of make the change and if the version change from
the initial which was read at the begining of the transaction an it is flagged
and the use can retry the transaction.

Inconsistency.

Inconsistency was mainly managed and avoided with the help of idempotency which 
help ensure not duplicate transaction could be mistakenly made.