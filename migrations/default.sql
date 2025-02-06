-- Drop existing tables, indexes, and types
DROP TABLE IF EXISTS mods_mod_tags CASCADE;
DROP TABLE IF EXISTS mod_gd_versions CASCADE;
DROP TABLE IF EXISTS dependencies CASCADE;
DROP TABLE IF EXISTS incompatibilities CASCADE;
DROP TABLE IF EXISTS mod_tags CASCADE;
DROP TABLE IF EXISTS mod_versions CASCADE;
DROP TABLE IF EXISTS mods_developers CASCADE;
DROP TABLE IF EXISTS mods CASCADE;
DROP TABLE IF EXISTS auth_tokens CASCADE;
DROP TABLE IF EXISTS developers CASCADE;
DROP TABLE IF EXISTS github_login_attempts CASCADE;
DROP INDEX IF EXISTS idx_version_id;
DROP TYPE IF EXISTS dependency_importance;
DROP TYPE IF EXISTS version_compare;
DROP TYPE IF EXISTS gd_version;
DROP TYPE IF EXISTS gd_ver_platform;
DROP TYPE IF EXISTS incompatibility_importance;
DROP TABLE IF EXISTS refresh_tokens;
DROP TABLE IF EXISTS github_web_logins;
DROP TABLE IF EXISTS mod_links;
DROP TABLE IF EXISTS mod_downloads;
DROP TABLE IF EXISTS mod_version_statuses;
DROP TYPE IF EXISTS mod_version_status;

-- Create types
CREATE TYPE dependency_importance AS ENUM ('required', 'recommended', 'suggested');
CREATE TYPE incompatibility_importance AS ENUM ('breaking', 'conflicting');
CREATE TYPE version_compare AS ENUM ('=', '>', '<', '>=', '=<');
CREATE TYPE gd_version as ENUM ('*', '2.113', '2.200', '2.204', '2.205');
CREATE TYPE gd_ver_platform as ENUM ('android32', 'android64', 'ios', 'mac', 'win');

-- Create tables
CREATE TABLE mods (
  id TEXT PRIMARY KEY NOT NULL,
  repository TEXT,
  changelog TEXT,
  about TEXT,
  image BYTEA,
  latest_version TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE mod_versions (
  id SERIAL PRIMARY KEY NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  version TEXT NOT NULL,
  download_link TEXT NOT NULL,
  hash TEXT NOT NULL,
  geode TEXT NOT NULL,
  early_load BOOLEAN NOT NULL DEFAULT false,
  api BOOLEAN NOT NULL DEFAULT false,
  validated BOOLEAN NOT NULL,
  mod_id TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  FOREIGN KEY (mod_id) REFERENCES mods(id)
);

CREATE UNIQUE INDEX idx_version_id ON mod_versions(version, mod_id);

CREATE TABLE mod_tags (
  id SERIAL PRIMARY KEY NOT NULL,
  name TEXT NOT NULL,
  display_name TEXT,
  is_readonly BOOLEAN NOT NULL DEFAULT false
);

-- Add unique constraint on the name column
ALTER TABLE mod_tags ADD CONSTRAINT unique_name UNIQUE (name);

-- Insert tags and update their display names if they already exist
INSERT INTO mod_tags (name, display_name, is_readonly) VALUES
  ('universal', 'Universal', false),
  ('gameplay', 'Gameplay', false),
  ('editor', 'Editor', false),
  ('offline', 'Offline', false),
  ('online', 'Online', false),
  ('enhancement', 'Enhancement', false),
  ('music', 'Music', false),
  ('interface', 'Interface', false),
  ('bugfix', 'Bugfix', false),
  ('utility', 'Utility', false),
  ('performance', 'Performance', false),
  ('customization', 'Customization', false),
  ('content', 'Content', false),
  ('developer', 'Developer', false),
  ('cheat', 'Cheat', false),
  ('paid', 'Paid', false),
  ('joke', 'Joke', false),
  ('modtober24', 'Modtober 2024', false),
  ('modtober24winner', 'Modtober 2024 Winner', true)
  ('api', 'API', false)
ON CONFLICT (name) 
DO UPDATE SET display_name = EXCLUDED.display_name;

CREATE TABLE mods_mod_tags (
  mod_id TEXT NOT NULL,
  tag_id INTEGER NOT NULL,
  PRIMARY KEY (mod_id, tag_id),
  FOREIGN KEY (mod_id) REFERENCES mods(id),
  FOREIGN KEY (tag_id) REFERENCES mod_tags(id)
);

CREATE TABLE mod_gd_versions (
  id SERIAL PRIMARY KEY NOT NULL,
  mod_id INTEGER NOT NULL,
  gd gd_version NOT NULL,
  platform gd_ver_platform NOT NULL,
  FOREIGN KEY (mod_id) REFERENCES mod_versions(id)
);

CREATE TABLE dependencies (
  dependent_id INTEGER NOT NULL,
  dependency_id TEXT NOT NULL,
  version TEXT NOT NULL,
  compare version_compare NOT NULL,
  importance dependency_importance NOT NULL,
  PRIMARY KEY (dependent_id, dependency_id),
  FOREIGN KEY (dependent_id) REFERENCES mod_versions(id),
  FOREIGN KEY (dependency_id) REFERENCES mods(id)
);

CREATE TABLE incompatibilities (
  mod_id INTEGER NOT NULL,
  incompatibility_id TEXT NOT NULL,
  version TEXT NOT NULL,
  compare version_compare NOT NULL,
  importance incompatibility_importance NOT NULL,
  PRIMARY KEY (mod_id, incompatibility_id),
  FOREIGN KEY (mod_id) REFERENCES mod_versions(id),
  FOREIGN KEY (incompatibility_id) REFERENCES mods(id)
);

CREATE TABLE developers (
  id SERIAL PRIMARY KEY NOT NULL,
  username TEXT NOT NULL,
  display_name TEXT NOT NULL,
  verified BOOLEAN DEFAULT false NOT NULL,
  admin BOOLEAN DEFAULT false NOT NULL,
  github_user_id BIGINT NOT NULL
);

CREATE TABLE mods_developers (
  mod_id TEXT NOT NULL,
  developer_id INTEGER NOT NULL,
  is_owner BOOLEAN DEFAULT false NOT NULL,
  PRIMARY KEY (mod_id, developer_id),
  FOREIGN KEY (mod_id) REFERENCES mods(id),
  FOREIGN KEY (developer_id) REFERENCES developers(id)
);

CREATE TABLE auth_tokens (
  token UUID DEFAULT gen_random_uuid() NOT NULL,
  developer_id INTEGER NOT NULL,
  PRIMARY KEY(token),
  FOREIGN KEY(developer_id) REFERENCES developers(id)
);

CREATE TABLE github_login_attempts (
  uid UUID DEFAULT gen_random_uuid() NOT NULL,
  ip inet NOT NULL,
  device_code TEXT NOT NULL,
  interval INTEGER NOT NULL,
  expires_in INTEGER NOT NULL,
  created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  last_poll TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
  PRIMARY KEY (uid, ip)
);

CREATE TABLE refresh_tokens (
  token TEXT NOT NULL,
  developer_id INTEGER NOT NULL,
  expires_at TIMESTAMPTZ NOT NULL,
  PRIMARY KEY(token),
  FOREIGN KEY(developer_id) REFERENCES developers(id)
);

CREATE TABLE github_web_logins (
  state UUID NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

CREATE TABLE mod_links (
  mod_id TEXT PRIMARY KEY NOT NULL,
  community TEXT,
  homepage TEXT,
  source TEXT,
  FOREIGN KEY (mod_id) REFERENCES mods(id)
);

CREATE TABLE mod_downloads (
  mod_version_id INTEGER NOT NULL,
  ip inet NOT NULL,
  time_downloaded timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (mod_version_id, ip),
  FOREIGN KEY (mod_version_id) REFERENCES mod_versions(id) ON DELETE CASCADE
);

-- Create indexes
CREATE INDEX idx_mods_id_latest_version ON mods(id, latest_version);
CREATE INDEX idx_mod_versions_mod_id ON mod_versions(mod_id);
CREATE INDEX idx_mod_versions_validated ON mod_versions(validated);
CREATE INDEX idx_mod_tags_name ON mod_tags(name);
CREATE INDEX idx_mods_mod_tags_mod_id ON mods_mod_tags(mod_id);
CREATE INDEX idx_dependencies_dependent_id ON dependencies(dependent_id);
CREATE INDEX idx_incompatibilities_mod_id ON incompatibilities(mod_id);
CREATE INDEX idx_developers_username ON developers(username);
CREATE INDEX idc_mods_developers_mod_id ON mods_developers(mod_id);
CREATE INDEX idx_auth_tokens_developer_id ON auth_tokens(developer_id);

CREATE TABLE IF NOT EXISTS github_loader_release_stats (
    id SERIAL PRIMARY KEY NOT NULL,
    total_download_count BIGINT NOT NULL,
    latest_loader_version TEXT NOT NULL,
    checked_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

create type mod_version_status as enum('pending', 'rejected', 'accepted', 'unlisted');

create table mod_version_statuses(
    id serial primary key,
    status mod_version_status not null default 'pending',
    info text,
    updated_at timestamptz not null default now(),
    mod_version_id integer not null,
    admin_id integer,
    foreign key (mod_version_id) 
        references mod_versions(id) 
        on delete cascade,
    foreign key (admin_id)
        references developers(id)
        on delete set null
);

create index mod_version_statuses_admin_id_idx on mod_version_statuses(admin_id);
create unique index mod_version_statuses_mod_version_id_idx on mod_version_statuses(mod_version_id);
create index mod_version_statuses_updated_at_idx on mod_version_statuses(updated_at);

alter table mod_versions add column status_id integer;

insert into mod_version_statuses (status, mod_version_id)
    select cast(case
        when validated = true then 'accepted'
        else 'pending'
    end AS mod_version_status) as status,
    id as mod_version_id
    from mod_versions;

update mod_versions set status_id = mvs.id
    from mod_version_statuses mvs
    where mod_versions.id = mvs.mod_version_id;

alter table mod_versions alter column status_id set not null;
alter table mod_versions 
    add foreign key (status_id) 
    references mod_version_statuses(id)
    deferrable;
alter table mod_versions drop column validated;

create index mod_versions_status_id_idx on mod_versions(status_id);

-- Other ALTER statements should follow in order, ensuring table columns and relationships are adjusted.

-- Insert and update statements for modifying data
-- (Place your `UPDATE` or `INSERT` statements after necessary schema updates)

-- Clean-up or additional ALTER operations (e.g., changing constraints, adding columns)
-- Ensure that data consistency is maintained.
