## Delegate call vs call

Delegate call can be difficult to wrap your head around, but think of it this way: a delegate call means "load the code from this address and run it". This means that, when you create the Safe tx with operation=delegatecall, you are telling the Safe to get the code from the contract whose address is provided and execute it.