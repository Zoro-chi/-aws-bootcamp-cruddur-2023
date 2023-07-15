-- this file was manually created
INSERT INTO public.users (display_name, handle, email, cognito_user_id)
VALUES
  ('Andrew Brown', 'andrewbrown', 'jagbetuyi+andrewbrown@hotmail.com', 'MOCK'),
  ('Junzy', 'JR', 'jagbetuyi001@gmail.com', 'MOCK'),
  ('Zoro', 'zorochi', 'jagbetuyi@hotmail.com', 'MOCK'),
  ('Londo Mollari','lmollari@centari.com' ,'londo' ,'MOCK');

INSERT INTO public.activities (user_uuid, message, expires_at)
VALUES
  (
    (SELECT uuid from public.users WHERE users.handle = 'zorochi' LIMIT 1),
    'This was imported as seed data!',
    current_timestamp + interval '10 day'
  ),
  (
    (SELECT uuid from public.users WHERE users.handle = 'andrewbrown' LIMIT 1),
    'Luke I am your Fajjjeeerr!',
    current_timestamp + interval '10 day'
  );
