# onbox_assistant

**Introduction**

Have you ever found yourself configuring a device that is located hundreds of miles away, when you get distracted and enter a command that causes you to lose connectivity? What do you do?

Wouldn't it be great if there was some sort of "intelligence" on the device that could recognize what happened, restore connectivity and alert you to which command caused the issue? 

In this post I am going to show you how we can leverage the capabilities of Cisco IOS XE and the Guest Shell container to run a Python script on-box to accomplish just that. 

For this demonstration I am using the Catalyst 9300 switch (C9300-24U) running IOS-XE Software Version 16.06.01.



**Logic Flowchart**

![alt text][logo]

[logo]: https://github.com/clintmann/onbox_assistant/blob/master/FlowChart-config_rollback.gif "Logic Flowchart"