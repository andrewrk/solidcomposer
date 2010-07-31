// inserts the items from incomingList into sortedList.
// assumes that each item in each list has an id property to sort by.
function mergeLists(sortedList, incomingList) {
    // sort incoming list
    var incomingCount = 0;
    if (incomingList.length) {
        incomingCount = incomingList.length;
    }
    if (incomingCount > 0) {
        incomingList.sort(function(a,b){
            return a.id - b.id;
        });
    }

    // return the index of where a new message should be inserted.
    // -1 if the message already exists
    function getMessageIndex(id) {
        // loop backwards through the array until we find the
        // slot for the new id
        var i;
        for (i=sortedList.length-1; i>=0; --i) {
            if (sortedList[i].id < id) {
                return i+1;
            } else if (sortedList[i].id === id) {
                return -1;
            }
        }
        // there are no messages
        return 0;
    }

    // insert the new messages into the sorted list
    // if the id is already in the array, discard it.
    var insertIndex;
    var i;
    for (i=0; i<incomingCount; ++i) {
        insertIndex = getMessageIndex(incomingList[i].id);
        if (insertIndex !== -1) {
            sortedList.splice(insertIndex, 0, incomingList[i]);
        }
    }
}
