# BUG-88: half cents rounded down

A line of 1 x 2.675 is invoiced as 2.67. Our terms say half a cent
rounds up, so it must be 2.68. Seen on invoice 5531.
