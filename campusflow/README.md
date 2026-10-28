# CampusFlow - Student Management System

CampusFlow is a complete Student Management System built with React, Express, and SQLite for local college use.

## Demo account

The application seeds a default administrator automatically.

Email: admin@campusflow.local
Password: Campus@123

This demo account is for local educational use only and should be changed before any public deployment.

## Local setup

1. Open PowerShell in the project folder.
2. Run:
   npm install
   npm --prefix client install
   npm --prefix server install
3. Create a local `.env` file from `.env.example` and replace the session secret.
4. Start the app:
   npm run dev
5. Open:
   Frontend: http://localhost:5173
   Backend: http://localhost:4000

## Available scripts

- `npm run dev` — run frontend and backend together
- `npm run build` — build the React frontend
- `npm test` — run backend tests

## Project structure

- `client/` — React + Vite frontend
- `server/` — Express + SQLite backend
- `server/data/` — SQLite database file

## Main features

- Admin login with session-based auth
- Dashboard with live database stats
- Student CRUD, search, filtering, pagination, sorting
- Department management with referential checks
- CSV export and printable report view
- Automated backend tests

## ER overview

Admins have many students? In this app the admin is only a login identity. Departments have many students, and students belong to one department.

- `admins` table: admin identity and bcrypt hash
- `departments` table: department details
- `students` table: student records referencing `departments.id`

This is a normalized schema with foreign keys, unique constraints, and indexes for search.

## Troubleshooting

- If the database is locked, stop any running server process and restart the app.
- If Vite cannot connect to the API, ensure the backend is running on port 4000 and the `CLIENT_URL` matches.
- If login fails, verify the seeded admin account or reset the `server/data/campusflow.db` file after backup.

## License

This project is for academic demonstration use.
