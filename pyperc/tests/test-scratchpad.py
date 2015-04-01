

def testish1():
    eventlist = []
    total_count = 0
    with open('events_all.txt', 'r') as fd:
        for ev in MegaEvent.stream(fd):
            eventlist.append(ev.to_dict())
            total_count += 1

    print 'read', total_count, 'events.'

    ev2 = []
    for evd in eventlist:
        ev2.append(MegaEvent.from_dict(evd))

    print 'reread', total_count, 'events.'

    sc = SortedCollection()
    for ev in ev2:
        sc.insert(ev.id, ev)

    print 'sorted'

    print 'top 50'
    for item in sc.find(limit=50, reverse=True):
        print item.id, item.code, item.description

    print 'top 50 minus 113'
    for item in sc.find(limit=50, reverse=True, filter=lambda item: item.code != 113):
        print item.id, item.code, item.description

    print 'bot 5 minus 113'
    for item in sc.find(limit=5, reverse=False, filter=lambda item: item.code != 113):
        print item.id, item.code, item.description

    last_id = 17964
    print '10 since last_id', last_id
    for item in sc.find_gt(last_id, limit=10, filter=lambda item: item.code != 113):
        print item.id, item.code, item.description

    find_id = last_id
    print 'finding', find_id
    item = sc.find_one(find_id)
    if item:
        print find_id, '===', item.id, item.code, item.description
    else:
        print find_id, 'not found!'

    find_id = -1
    print 'finding', find_id
    item = sc.find_one(find_id)
    if item:
        print find_id, '===', item.id, item.code, item.description
    else:
        print find_id, 'not found!'

    find_id = 0
    print 'finding', find_id
    item = sc.find_one(find_id)
    if item:
        print find_id, '===', item.id, item.code, item.description
    else:
        print find_id, 'not found!'

    find_id = 1
    print 'finding', find_id
    item = sc.find_one(find_id)
    if item:
        print find_id, '===', item.id, item.code, item.description
    else:
        print find_id, 'not found!'

    find_id = 20000
    print 'finding', find_id
    item = sc.find_one(find_id)
    if item:
        print find_id, '===', item.id, item.code, item.description
    else:
        print find_id, 'not found!'

def testish2():
    sc = SortedCollection(limit=10)
    total_count = 0
    with open('events_all.txt', 'r') as fd:
        for ev in MegaEvent.stream(fd):
            sc.insert(ev.id, ev)
            total_count += 1

    print 'loaded', total_count, 'events into the limited collection'
    for item in sc.find(reverse=True):
        print item.id, item.code, item.description
    

if __name__ == '__main__':
    testish2()



import sys
for i in range(10):
    event = pa.events.data[i]
    print pa.events.keys[i], event.id, event.code, event.description

for i in range(1,10):
    event = pa.events.data[-i]
    print pa.events.keys[-i], event.id, event.code, event.description

since = 19900
print 'testing since', since
if since in pa.events.keys:
    print "it's in the keys"
else:
    print "it is not in the keys"
item = pa.events.find_one(since)
print item

since = 19899
print 'testing since', since
if since in pa.events.keys:
    print "it's in the keys"
else:
    print "it is not in the keys"
item = pa.events.find_one(since)
print item
print 'find_ge() ---------->'
for item in pa.events.find_gt(since):
    print item
print '---------------------'

