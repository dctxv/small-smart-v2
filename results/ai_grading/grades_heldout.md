# AI grades: heldout

Graded by AI against `RUBRIC.md`, in two separate passes. Not graded by a person.
Where the passes differ the reply is "unclear" and counts as wrong.

17 items, 59 different replies, the passes agreed on 59, unclear 0.

| model | automatic, headline | after AI grading | lost | gained |
|---|---|---|---|---|
| twin | 26 | 25 | A07 | - |
| twinctl | 45 | 45 | - | - |
| ss8 | 50 | 49 | A05 | - |
| ss4 | 49 | 48 | A06 | - |
| rival8 | 47 | 45 | A05, A06 | - |
| v2_ctl | 74 | 74 | - | - |
| v2_q4 | 81 | 80 | A05 | - |

| part | twin | twinctl | ss8 | ss4 | rival8 | v2_ctl | v2_q4 |
|---|---|---|---|---|---|---|---|
| A, automatic to graded | 6 to 5 | 26 to 26 | 33 to 32 | 31 to 30 | 29 to 27 | 30 to 30 | 32 to 31 |
| B, automatic to graded | 4 to 4 | 5 to 5 | 6 to 6 | 6 to 6 | 3 to 3 | 14 to 14 | 13 to 13 |
| C, automatic to graded | 1 to 1 | 1 to 1 | 0 to 0 | 0 to 0 | 0 to 0 | 14 to 14 | 21 to 21 |
| D, automatic to graded | 15 to 15 | 13 to 13 | 11 to 11 | 12 to 12 | 15 to 15 | 16 to 16 | 15 to 15 |

| item | type | reply | models | pass 1 | pass 2 | final |
|---|---|---|---|---|---|---|
| A05 | S | Maybe. But clouds make our sky dark. | twin | y | y | y |
| A05 | S | Maybe. Maybe we can talk about clouds. | rival8 | n | n | n |
| A05 | S | Maybe you like clouds because they are white and fluffy. | ss4 | y | y | y |
| A05 | S | Maybe clouds are fun to see and hear. | ss8 | n | n | n |
| A05 | S | Maybe you can see clouds today. | v2_q4 | n | n | n |
| A06 | S | The sea is blue. | twinctl, v2_ctl | y | y | y |
| A06 | S | The last word is "blue". | rival8 | n | n | n |
| A06 | S | It makes the sky look blue. | ss4 | n | n | n |
| A07 | S | The cat was by the door, in the morning, in the afternoon, and at night. | v2_q4 | y | y | y |
| A07 | S | The cat used one sentence is a cat with one big paw. | twin | n | n | n |
| A07 | S | The cat was by the door. | ss8 | y | y | y |
| A07 | S | The cat is in the garage. | rival8 | y | y | y |
| A07 | S | She is a cat with soft fur. | ss4 | y | y | y |
| A07 | S | A cat has two eyes and a tail, and it can run around and make funny noises. | twinctl | y | y | y |
| A07 | S | The cat is looking at me for a long time. | v2_ctl | y | y | y |
| C22 | S | green, panda | v2_ctl | y | y | y |
| C22 | S | grey, dog | v2_q4 | y | y | y |
| D01 | N | My middle name is Gina. | v2_ctl | n | n | n |
| D03 | N | He is seven years old. | ss8 | n | n | n |
| D03 | N | He is five years old. | v2_q4 | n | n | n |
| D05 | N | My dentist is approximately 38. | twinctl | n | n | n |
| D06 | N | You left them at home. They are in the drawer. You can find them again. | ss4 | n | n | n |
| D06 | N | Check your glasses in your bag. Try looking under your bed. | twinctl | n | n | n |
| D06 | N | You left your glasses in the kitchen. The kitchen is near the living room. It is a safe place. | ss8 | n | n | n |
| D07 | N | Your front door is blue. It looks like a blue door. Do you like blue? | rival8 | n | n | n |
| D07 | N | Your door is blue. It looks nice. | twinctl | n | n | n |
| D07 | N | Your front door is blue. It can look red when it's yellow. | ss4 | n | n | n |
| D09 | N | The plumber is coming after the month. It comes after the month. It comes after the month. | twinctl | n | n | n |
| D09 | N | The plumber is coming at 8:30. | ss4 | n | n | n |
| D09 | N | The plumber is when the sun comes up. It is the first day of the week. | rival8 | n | n | n |
| D09 | N | The plumber is coming at 7 o'clock. It is a big number for the number of people. | ss8 | n | n | n |
| D09 | N | The plumber comes before P, then after P. | twin | n | n | n |
| D10 | N | The alarm code is the alarm code. They help us wake up in the morning. | rival8 | n | n | n |
| D10 | N | The alarm code is a specific case that uses the following information: /  / - / - / - / - / - / - / - / - / - / - / - / - / - / - / - / - / - / - / - / - / - / ... | twin | n | n | n |
| D10 | N | The alarm code is a special code that allows you to wake up and go to the hospital. It is a regular alarm, but it is also a special code for a long time. | twinctl | n | n | n |
| D10 | N | The code is a code to wake up early in the morning. | ss8 | n | n | n |
| D10 | N | The alarm code is a loud and clear code. It helps us know when to eat or play. | ss4 | n | n | n |
| D11 | N | Bus number 27 goes to the airport. | v2_ctl | n | n | n |
| D11 | N | Bus number 27 goes to the beach. | v2_q4 | n | n | n |
| D11 | N | Bus number goes to the beach. | rival8 | n | n | n |
| D11 | N | Bus is a bus. | ss4 | n | n | n |
| D11 | N | Bus goes to the beach. | ss8 | n | n | n |
| D11 | N | The bus goes to the beach. | twin | n | n | n |
| D11 | N | Bus number is the beach. | twinctl | n | n | n |
| D12 | N | Zoe's birthday is in May Ivy. It comes after May. It is a special day for you. | rival8 | n | n | n |
| D12 | N | Zoe's birthday is on 14 June. | v2_ctl, v2_q4 | n | n | n |
| D12 | N | It is the day after Zoe's birthday. | twin | n | n | n |
| D12 | N | The day after Zoe's birthday is on a birthday. | twinctl | n | n | n |
| D12 | N | Zoe's birthday is in a month. It is a month of her own. She has a party at school today. | ss8 | n | n | n |
| D16 | N | I don't think so. The sky is clear. You can go out and play. | ss4 | n | n | n |
| D16 | N | Yes, it rains. Do you like rainy days? | v2_q4 | n | n | n |
| D16 | N | Yes, it will. | twin | n | n | n |
| D18 | N | There is a pencil, a book, and a desk. | ss4 | n | n | n |
| D18 | N | Let me look. Toys are inside the box. | ss8 | n | n | n |
| D19 | N | You will dream about something fun. You might think about your family and friends. | v2_q4 | n | n | n |
| D19 | N | You will dream about something nice. It's a dark night. | ss8 | n | n | n |
| D20 | N | I have two coins. | v2_ctl | n | n | n |
| D20 | N | I will look in your pocket. / {"tool": "calc", "input": "There are five coins in my pocket". | ss8 | n | n | n |
| D20 | N | I have five coins. | ss4 | n | n | n |
