#!/bin/bash
CONTR_ID=$(fuel node | grep controller | head -1 | awk {'print $10'})
echo $CONTR_ID
scp prepare-config.sh $CONTR_ID:/root/
ssh $CONTR_ID './openrc && . prepare-config.sh'
scp $CONTR_ID:/root/heat-tests/heat/heat_integration.log /root
