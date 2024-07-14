# Queue management: Standard endpoints

We do not live in a perfect world. Things can and do go wrong, the world of
software and distributed systems is no exception. Any tools that can help in the
mitigation of loss when things do go wrong, are invaluable.

Therefore, Ecosystem provides a host of standard endpoints in your applications.
Ripe and ready for you to use, when you need to get down and dirty with queues.

I am listing them here, for the sake of completeness, and the fact that you might
want to create your own queue management scripts. However, you'll most likely
want to use [the Ecosystem command line tool](../command_line_tool.md) before doing that.

---
## For `queued_endpoint`
- `eco.queued_handler.data`
  - For getting information about a queue.
- `eco.queued_handler.receiving.pause`
  - For stopping the receiving of messages.
  - The causes your application to respond to clients, with a server-busy response,
    rather than allowing the message to enter the queue.
- `eco.queued_handler.receiving.unpause`
  - For allowing receiving again.
- `eco.queued_handler.processing.pause`
  - For stopping the processing of a queue.
  - In other words, the queue will still get messages put into it, they just won't
    be processed.
- `eco.queued_handler.processing.unpause`
  - For allowing processing again.
- `eco.queued_handler.all.pause`
  - This stops both the receiving and processing of queues.
- `eco.queued_handler.all.unpause`
  - This resumes both receiving and processing of queues.
- `eco.queued_handler.errors.get_first_10`
  - Gets you the UUIDs of the first 10 messages in the `error` database of a queue.
- `eco.queued_handler.errors.reprocess.all`
  - Moves all messages in the `error` database of a queue, to the `pending` database.
- `eco.queued_handler.errors.clear`
  - DELETES all entries in the `error` database of a queue.
- `eco.queued_handler.errors.reprocess.one`
  - Moves one specified message, from the `error` database to the back of the
    `pending` database.
- `eco.queued_handler.errors.pop_request`
  - DELETES one specified message from the `error` database of a queue
- `eco.queued_handler.errors.inspect_request`
  - Allows you to look at one specified message in the `error` database of a queue

---
### For `queued_sender`
- `eco.queued_sender.data`
    - For getting information about a queue.
- `eco.queued_sender.send_process.pause`
  - Stops the processing of messages in the queue.
  - i.e. Stops sending messages in the `pending` database of a queue.
- `eco.queued_sender.send_process.unpause`
  - Resumes the processing of messages in the queue.
- `eco.queued_sender.errors.get_first_10`
  - Gets you the UUIDs of the first 10 messages in the `error` database of a queue.
- `eco.queued_sender.errors.reprocess.all`
  - Moves all messages in the `error` database of a queue, to the `pending` database.
- `eco.queued_sender.errors.clear`
  - DELETES all entries in the `error` database of a queue.
- `eco.queued_sender.errors.reprocess.one`
  - Moves one specified message, from the `error` database to the back of the
    `pending` database.
- `eco.queued_sender.errors.pop_request`
  - DELETES one specified message from the `error` database of a queue
- `eco.queued_sender.errors.inspect_request`
  - Allows you to look at one specified message in the `error` database of a queue
