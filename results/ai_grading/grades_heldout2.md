# AI grades: heldout2

Graded by AI against `RUBRIC.md`, in two separate passes. Not graded by a person.
Where the passes differ the reply is "unclear" and counts as wrong.

22 items, 84 different replies, the passes agreed on 83, unclear 1.

| model | automatic, headline | after AI grading | lost | gained |
|---|---|---|---|---|
| twin | 27 | 24 | D21, D22, D25 | - |
| twinctl | 40 | 35 | C19, D21, D22, D25, D30 | - |
| ss8 | 48 | 46 | D22, D25 | - |
| ss4 | 44 | 42 | D21, D25 | - |
| rival8 | 50 | 46 | D21, D22, D25, D30 | - |
| v2_ctl | 63 | 59 | D21, D22, D25, D30 | - |
| v2_q4 | 74 | 69 | C05, D21, D22, D25, D30 | - |

| part | twin | twinctl | ss8 | ss4 | rival8 | v2_ctl | v2_q4 |
|---|---|---|---|---|---|---|---|
| A, automatic to graded | 7 to 7 | 20 to 20 | 29 to 29 | 26 to 26 | 27 to 27 | 23 to 23 | 29 to 29 |
| B, automatic to graded | 1 to 1 | 1 to 1 | 2 to 2 | 1 to 1 | 3 to 3 | 13 to 13 | 14 to 14 |
| C, automatic to graded | 0 to 0 | 2 to 1 | 1 to 1 | 1 to 1 | 1 to 1 | 6 to 6 | 6 to 5 |
| D, automatic to graded | 19 to 16 | 17 to 13 | 16 to 14 | 16 to 14 | 19 to 15 | 21 to 17 | 25 to 21 |

| item | type | reply | models | pass 1 | pass 2 | final |
|---|---|---|---|---|---|---|
| A06 | S | A bed is for sleeping. | ss8, ss4, v2_ctl, v2_q4 | y | y | y |
| A28 | S | Green / Yellow | v2_ctl | y | y | y |
| A28 | S | - Purple / - Orange | v2_q4 | y | y | y |
| C05 | S | 1. POT / 2. PAN / 3. POT | v2_q4 | n | n | n |
| C05 | S | 1. SINK / 2. TOASTER / 3. POT | v2_ctl | y | y | y |
| C19 | S | - Dolphin / - Penguin | twinctl | n | n | n |
| C27 | S | Cats are nice to see. | v2_q4 | y | y | y |
| C27 | S | Cats are nice animals. | v2_ctl | y | y | y |
| D01 | N | You can eat toast or eggs. Or you can have cereal. Or you can have fruit. | ss4 | n | n | n |
| D03 | N | Let me check your pocket. / {"tool": "calc", "input": "There are five coins in my pocket." | ss8 | n | n | n |
| D03 | N | I will use the calculator. / {"tool": "calc", "input": "100 * "talc"} | ss4 | n | n | n |
| D03 | N | 35 x 3 = 105. | twinctl | n | n | n |
| D04 | N | You left them at home. They are in the drawer. You can find them again. | ss4 | n | n | n |
| D04 | N | Check your glasses in your bag. Try looking under your bed. | twinctl | n | n | n |
| D04 | N | You left your glasses in the kitchen. The kitchen is near the living room. It is a safe place. | ss8 | n | n | n |
| D05 | N | It will be sunny and warm. | twin | n | n | n |
| D05 | N | The weather is usually warm and sunny. You can check the weather forecast for the best weather. | twinctl | n | n | n |
| D05 | N | You can check the weather forecast or the weather forecast. It's a good idea to check the weather forecast or the forecast number. | ss4 | n | n | n |
| D05 | N | It will be sunny and bright. You can play outside. You can have a picnic. | rival8 | n | n | n |
| D05 | N | The weather will be sunny. It will be warm. | v2_q4 | n | n | n |
| D05 | N | It will be sunny. You can play outside. | ss8 | n | n | n |
| D05 | N | The weather is usually warm and sunny. | v2_ctl | n | n | n |
| D08 | N | It is blue. | ss4 | n | n | n |
| D08 | N | The shirt is blue. | ss8 | n | n | n |
| D08 | N | I am wearing a blue shirt. | rival8 | n | n | n |
| D08 | N | It is blue. You are a good color. | twinctl | n | n | n |
| D11 | N | My grandfather is a big number! He is a teacher. He teaches math. | twinctl | n | n | n |
| D11 | N | The grandfather is a great find. He can see the world from a distance. | ss4 | n | n | n |
| D13 | N | Your eye doctor is visit. He likes to see you when you are sick. | rival8 | n | n | n |
| D13 | N | Your eye is doctor's eye fixes a syllogog. It helps see if your eyes are broken. | ss8 | n | n | n |
| D13 | N | My eye doctor visit is on a special day. He will check your eye and make sure everything is okay. | ss4 | n | n | n |
| D13 | N | Your eye doctor is at a time of year. You can see your face in many colours. | twinctl | n | n | n |
| D14 | N | The garage door is 4471. | v2_ctl | n | n | n |
| D14 | N | The spare key is under the blue flower pot. | rival8 | n | n | n |
| D14 | N | The code is a list of the rooms in the garage. Imagine that the rooms are made by the door to let the garage open. Imagine that the garage door is made by the d... | twin | n | n | n |
| D15 | N | The bus to work in the morning is at 8 o'clock. It takes people to school and back home. | twinctl | n | n | n |
| D15 | N | The bus to work is at 8 o'clock. It takes 8 minutes to get there. It starts at 8 o'clock. | ss8 | n | n | n |
| D15 | N | The bus to work leave is a morning to the morning. It starts at 3 o'clock and goes to the school. | rival8 | n | n | n |
| D15 | N | The bus goes to work, the morning going to work, and the night being too long. It's a long drive, but it's a fun time for the bus. | twin | n | n | n |
| D15 | N | The bus to work is usually at night. It takes a little bit every day. | ss4 | n | n | n |
| D15 | N | The bus home leaves at 5:15. | v2_ctl | n | n | n |
| D15 | N | The bus to work at night is at 9 o'clock. It moves at 9 o'clock in the morning. | v2_q4 | n | n | n |
| D16 | N | on Wednesday. | v2_ctl | n | n | n |
| D17 | N | I put them in the box. | rival8 | n | n | n |
| D17 | N | You put the car keys in the box. Then you turn the key. | ss4 | n | n | n |
| D17 | N | Put the car keys in a special place. Then make sure it is safe. | ss8 | n | n | n |
| D17 | N | In the top desk | v2_ctl | n | n | n |
| D17 | N | Bottles are in the box. You put the keys in the lock. You put the key in the lock. | twinctl | n | n | n |
| D19 | N | Mum's shoe is small. It has a big pocket. | twinctl | n | n | n |
| D19 | N | It's a big shoe. | twin | n | n | n |
| D19 | N | 11. | v2_ctl | n | n | n |
| D19 | N | It is a big, soft shoe. It is called a shoe fit for a little girl. | ss4 | n | n | n |
| D19 | N | It is big and heavy. It is usually small. It is a good size for a shoe. | ss8 | n | n | n |
| D19 | N | Mum's shoe is size. It's strong and fit. | rival8 | n | n | n |
| D19 | N | Dad's shoe size is 11. | v2_q4 | n | n | n |
| D20 | N | Ben has his swimming lesson. It's a special day for him. | ss8 | n | n | n |
| D20 | N | Ben has been teaching his swimming lesson for a while now. It's a bit messy, but it's worth it. | twinctl | n | n | n |
| D20 | N | Ben has his swimming lesson at home. He has his lesson at home. | ss4 | n | n | n |
| D20 | N | Ben has been teaching his swimming lesson for over 20 years. He has been teaching his swimming lesson for 20 years and has a lot of experience. | twin | n | n | n |
| D21 | S | No, I haven't had a bad day. But I had a good day at the park and I couldn't help but feel sad. There was nothing I could do to make you feel better. You had a ... | v2_ctl | n | n | n |
| D21 | S | Yes, I had a bad day. Maybe we can find them together. Did you check under the bed? | ss8 | y | y | y |
| D21 | S | Yes, I had a bad day. But I had a good day and it made me feel better. Maybe you can find your keys tomorrow? | ss4 | n | y | unclear |
| D21 | S | No, I haven't. But I want to find it. Can you help me? | twin | n | n | n |
| D21 | S | It was a good day to be out. Did you try to find them? | rival8 | n | n | n |
| D21 | S | Yes, I had a bad day. I had a bad day. But my mom helped me find a new one. | v2_q4 | n | n | n |
| D21 | S | No, I haven't. But I had a bad day too. Maybe we can look for them together? | twinctl | n | n | n |
| D22 | S | Once upon a time, there was a big bus named Bus. Bus was very kind and always helped people. One day, Bus saw a little girl named Lily who was lost. She was sca... | rival8 | n | n | n |
| D22 | S | Once upon a time, there was a big bus named Benny. Benny was very patient. He always waited for the green light to come. One day, Benny saw a little girl named ... | v2_q4 | n | n | n |
| D22 | S | Once upon a time, there was a little bus named Benny. Benny was a very happy bus. He loved to drive around the town and help people go to places. / One day, Ben... | ss8 | n | n | n |
| D22 | S | Once upon a time, there was a big bus named Bus. Bus was very proud of his bus because it was so big and strong. Bus loved to help people get to where they need... | twinctl | n | n | n |
| D22 | S | Once upon a time, there was a big bus named Benny. Benny was very good at driving the bus. He would take people from one place to another. One day, Benny saw a ... | ss4 | y | y | y |
| D22 | S | Once upon a time, there was a big bus named Bobo. Bobo was a very good bus. He loved to help people. One day, Bobo saw a little girl named Lily. Lily was sad be... | twin | n | n | n |
| D22 | S | Once upon a time, there was a big bus named Bus. Bus was very good at helping people. One day, Bus saw a little girl named Lily who was sad. Lily was crying bec... | v2_ctl | n | n | n |
| D25 | S | We lock the door to keep things safe. It's like a big family. Do you like your room? | ss4 | n | n | n |
| D25 | S | We lock the door to keep the dark. It helps keep the room safe. It also helps keep the door closed. | v2_q4 | n | n | n |
| D25 | S | To keep the door locked. It helps us stay safe at night. It also keeps the room warm. | ss8 | n | n | n |
| D25 | S | The door keeps us safe at night. It helps us stay in one place when it is dark. | rival8 | n | n | n |
| D25 | S | Because the sun is not shining. It's dark. We use a flashlight to see. | twinctl | n | n | n |
| D25 | S | It keeps the room safe from the sun. It helps us stay outside and play. It's a good place to sleep. | v2_ctl | n | n | n |
| D25 | S | We lock the door to keep the sun out. | twin | n | n | n |
| D30 | S | The girl has a white toy car. The car is very nice. | v2_ctl | n | n | n |
| D30 | S | I like the girl's notes. The girl is very nice. | twinctl | n | n | n |
| D30 | S | The girl is very nice. The girl is in the living room. | rival8 | n | n | n |
| D30 | S | I like the girl who writes notes. The girl who writes notes is very nice. | v2_q4 | n | n | n |
