# KidVault
A gamified platform where parents assign money-linked learning challenges and kids earn, manage, and understand real-world finances through rewards and progress.
## Problem Statement
Children today have early access to digital money and online payments, but lack the knowledge and skills to manage it responsibly. This results in poor spending habits and little understanding of the value of money, while parents lack effective tools to teach financial discipline in a safe and engaging way. 
Basically, how can we create a fun, engaging, and controlled platform that helps children learn financial literacy and responsible money management through real-life simulation while enabling parents to guide and monitor their learning?
## Proposed Solution
* Core Idea:
A gamified financial learning platform where children don’t just receive money — they earn, manage, and understand it.
Designed to build real-world money habits in a safe, guided environment.

* Smart Money Management: 
Kids use earned credits to:
Save for goals
Spend on rewards
Make choices between needs vs wants
Builds early habits of saving, budgeting, and decision-making.

* Controlled Digital Transactions: 
The platform can extend to allow safe, parent-approved digital transactions (UPI-based).
Children get real exposure to digital payments while staying in a secure and monitored system.
Helps bridge the gap between learning and real-world financial usage.

* Parent Involvement: 
Parents actively guide the process by:
Assigning tasks and challenges
Setting reward values
Approving transactions and rewards
Tracking progress and behavior
Shifts parenting from “giving money” → “teaching money management.”

* Gamified Experience: 
Engaging features like:
Levels, XP, badges, and rewards
Unlockable achievements
Retry-based learning with feedback
Makes financial education fun, interactive, and addictive (in a good way).

## Tech Stack
* Python powers the full backend. All application logic, request handling, authentication checks, and database interactions are written in Python.

* Flask is the web framework. It handles incoming HTTP requests and routes them to backend functions, making it the main server layer of the app.

* Flask Blueprints organize the backend into feature-based modules. Instead of putting all routes in one file, features like auth, challenges, progress, rewards, and questions are separated into their own files for cleaner structure.

* app.py is the main entry point. It creates the Flask app, loads configuration, registers all Blueprints, and runs the development server on port 5000.

* Flask Session is used for login state management. After authentication, key user data such as user_id, role, and name is stored in the session, and protected routes verify this before allowing access.

* SECRET_KEY secures the session system. It signs the session cookie so authentication data cannot be tampered with easily.

* MySQL is the database. It stores structured application data such as users, challenges, levels, quiz questions, progress records, and rewards.

* mysql-connector-python is the Python driver used to connect Flask with MySQL and execute SQL queries.

* database.py provides a reusable query helper. This keeps database access simple and avoids repeating connection logic across route files.

* Raw SQL is used instead of an ORM. This gives direct control over queries and keeps the project lightweight, which is practical for a hackathon-style MVP.

* Parameterized queries using %s placeholders improve security by preventing SQL injection.

* config.py centralizes important settings such as database credentials, SECRET_KEY, and QUESTIONS_PER_LEVEL, so sensitive or reusable values are not hardcoded across files.

# DEMO LINK
## Key Features and Uniqueness
* Gamified earn–learn system where kids answer quizzes and complete tasks to earn rewards
* Topic-wise rewards: correct answers earn money set by parents for each specific topic
* Simulated wallet with save/spend choices to build real financial habits
* UPI-based payments with parental approval, ensuring safe real-world exposure
* Smart parent control panel for assigning tasks, setting limits, and tracking activity
* Interactive kid dashboard with balance, progress, and achievements
* Built-in spending discipline through limits, approvals, and goal-based rewards
* Uniqueness: The most unique feature is the combination of topic-based earning with controlled UPI spending — kids don’t just learn about money, they earn it by answering correctly and use it under parental supervision.

“It turns financial learning into real-world practice by linking knowledge → earning → spending in a safe, guided system.”

## Feasibility and Reliability
Feasibility
* Can be built within a hackathon timeframe using basic full-stack tools
* Core features rely on:
** Simple quiz logic
** Credit-based reward system
** Basic database operations
* No dependency on complex AI or real payment systems

Reliability
* Fully controlled system with parent approval at every reward stage
* No real money involved → eliminates financial risk
* Structured environment ensures:
* Safe usage
* Predictable behavior
* Data consistency

## Market Opportunities
* Rising need for financial literacy at a young age
* Growth of EdTech + FinTech combined solutions
* Parents of children (6–16 years)
* Schools and educational institutions
* Increased smartphone and UPI exposure among kids
* Lack of structured financial education tools
* Growing awareness of money management skills
