-- 아두마켓 데이터베이스 구조
-- Supabase SQL Editor에 붙여넣어 실행해도 됩니다. 여러 번 실행해도 안전합니다.

-- 1) 카테고리
create table if not exists public.categories (
  id         bigint generated always as identity primary key,
  slug       text not null unique,
  name       text not null,
  sort_order int  not null default 0
);

-- 2) 상품
create table if not exists public.products (
  id             bigint generated always as identity primary key,
  slug           text not null unique,
  name           text not null,
  category_id    bigint references public.categories(id) on delete set null,
  price          int  not null check (price >= 0),
  stock          int  not null default 0 check (stock >= 0),
  description    text,
  specs          text[] not null default '{}',
  image_url      text,
  devicemart_url text,
  image_source   text,
  image_license  text,
  image_author   text,
  created_at     timestamptz not null default now()
);

-- 3) 회원 정보 (로그인 계정은 Supabase Auth의 auth.users에 저장됨)
create table if not exists public.profiles (
  id         uuid primary key references auth.users(id) on delete cascade,
  email      text not null,
  name       text,
  is_admin   boolean not null default false,
  created_at timestamptz not null default now()
);

-- 4) 장바구니
create table if not exists public.cart_items (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references auth.users(id) on delete cascade,
  product_id bigint not null references public.products(id) on delete cascade,
  quantity   int not null check (quantity > 0),
  created_at timestamptz not null default now(),
  unique (user_id, product_id)
);

-- 5) 주문
create table if not exists public.orders (
  id          bigint generated always as identity primary key,
  user_id     uuid not null references auth.users(id) on delete cascade,
  total_price int  not null,
  status      text not null default '주문완료',
  recipient   text not null,
  phone       text not null,
  address     text not null,
  created_at  timestamptz not null default now()
);

-- 6) 주문 상품 (주문 당시 이름과 가격을 그대로 남김)
create table if not exists public.order_items (
  id           bigint generated always as identity primary key,
  order_id     bigint not null references public.orders(id) on delete cascade,
  product_id   bigint references public.products(id) on delete set null,
  product_name text not null,
  price        int  not null,
  quantity     int  not null
);

-- 보안(RLS): 상품과 카테고리만 누구나 읽을 수 있고,
-- 장바구니·주문·회원 정보는 Flask 서버(service_role 키)만 다룰 수 있습니다.
alter table public.categories  enable row level security;
alter table public.products    enable row level security;
alter table public.profiles    enable row level security;
alter table public.cart_items  enable row level security;
alter table public.orders      enable row level security;
alter table public.order_items enable row level security;

drop policy if exists "누구나 카테고리 조회" on public.categories;
create policy "누구나 카테고리 조회" on public.categories for select using (true);

drop policy if exists "누구나 상품 조회" on public.products;
create policy "누구나 상품 조회" on public.products for select using (true);

-- 주문하기: 재고 확인 → 주문 생성 → 재고 차감 → 장바구니 비우기를 한 번에 처리
create or replace function public.place_order(
  p_user_id uuid, p_recipient text, p_phone text, p_address text
) returns bigint
language plpgsql
set search_path = public
as $$
declare
  v_order_id bigint;
  v_total    int;
  v_item     record;
begin
  -- 장바구니 상품을 잠가서 동시에 주문해도 재고가 꼬이지 않게 함
  for v_item in
    select c.product_id, c.quantity, p.name, p.price, p.stock
    from cart_items c join products p on p.id = c.product_id
    where c.user_id = p_user_id
    for update of p
  loop
    if v_item.stock < v_item.quantity then
      raise exception '재고 부족: % (남은 수량 %개)', v_item.name, v_item.stock;
    end if;
  end loop;

  select coalesce(sum(c.quantity * p.price), 0) into v_total
  from cart_items c join products p on p.id = c.product_id
  where c.user_id = p_user_id;

  if v_total = 0 then
    raise exception '장바구니가 비어 있습니다';
  end if;

  insert into orders (user_id, total_price, recipient, phone, address)
  values (p_user_id, v_total, p_recipient, p_phone, p_address)
  returning id into v_order_id;

  insert into order_items (order_id, product_id, product_name, price, quantity)
  select v_order_id, p.id, p.name, p.price, c.quantity
  from cart_items c join products p on p.id = c.product_id
  where c.user_id = p_user_id;

  update products p set stock = p.stock - c.quantity
  from cart_items c
  where c.user_id = p_user_id and c.product_id = p.id;

  delete from cart_items where user_id = p_user_id;

  return v_order_id;
end;
$$;

-- 주문 함수는 서버(service_role)만 실행 가능
revoke execute on function public.place_order(uuid, text, text, text) from public, anon, authenticated;
grant  execute on function public.place_order(uuid, text, text, text) to service_role;

-- 관리자가 올리는 상품 이미지 저장소 (누구나 볼 수 있는 공개 버킷)
insert into storage.buckets (id, name, public)
values ('product-images', 'product-images', true)
on conflict (id) do nothing;
