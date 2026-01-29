# Buffer management: Standard endpoints

We do not live in a perfect world. Things can and do go wrong, the world of
software and distributed systems is no exception. Any tools that can help in the
mitigation of loss when things do go wrong, are invaluable.

Therefore, Ecosystem provides a host of standard endpoints in your applications.
Ripe and ready for you to use when you need to get down and dirty with buffers.

I am listing them here for the sake of completeness, and the fact that you might
want to create your own buffer management scripts. However, you'll most likely
want to use [the Ecosystem command line tool](../command_line_tool.md) before doing that.

---
## For `buffered_endpoint`
- `eco.buffered_handler.data`
  - For getting information about a buffer.
- `eco.buffered_handler.receiving.pause`
  - For stopping the receiving of messages.
  - This causes your application to respond to clients, with a server-busy response,
    rather than allowing the message to enter the buffer.
- `eco.buffered_handler.receiving.unpause`
  - For allowing receiving again.
- `eco.buffered_handler.processing.pause`
  - For stopping the processing of a buffer.
  - In other words, the buffer will still get messages put into it, they just won't
    be processed.
- `eco.buffered_handler.processing.unpause`
  - For allowing processing again.
- `eco.buffered_handler.all.pause`
  - This stops both the receiving and processing of buffers.
- `eco.buffered_handler.all.unpause`
  - This resumes both receiving and processing of buffers.
- `eco.buffered_handler.errors.get_first_10`
  - Gets you the UUIDs of the first 10 messages in the `error` database of a buffer.
- `eco.buffered_handler.errors.reprocess.all`
  - Moves all messages in the `error` database of a buffer, to the `pending` database.
- `eco.buffered_handler.errors.clear`
  - DELETES all entries in the `error` database of a buffer.
- `eco.buffered_handler.errors.reprocess.one`
  - Moves one specified message, from the `error` database to the back of the
    `pending` database.
- `eco.buffered_handler.errors.pop_request`
  - DELETES one specified message from the `error` database of a buffer
- `eco.buffered_handler.errors.inspect_request`
  - Allows you to look at one specified message in the `error` database of a buffer

---
### For `buffered_sender`
- `eco.buffered_sender.data`
    - For getting information about a buffer.
- `eco.buffered_sender.send_process.pause`
  - Stops the processing of messages in the buffer.
  - i.e. Stops sending messages in the `pending` database of a buffer.
- `eco.buffered_sender.send_process.unpause`
  - Resumes the processing of messages in the buffer.
- `eco.buffered_sender.errors.get_first_10`
  - Gets you the UUIDs of the first 10 messages in the `error` database of a buffer.
- `eco.buffered_sender.errors.reprocess.all`
  - Moves all messages in the `error` database of a buffer, to the `pending` database.
- `eco.buffered_sender.errors.clear`
  - DELETES all entries in the `error` database of a buffer.
- `eco.buffered_sender.errors.reprocess.one`
  - Moves one specified message, from the `error` database to the back of the
    `pending` database.
- `eco.buffered_sender.errors.pop_request`
  - DELETES one specified message from the `error` database of a buffer
- `eco.buffered_sender.errors.inspect_request`
  - Allows you to look at one specified message in the `error` database of a buffer
