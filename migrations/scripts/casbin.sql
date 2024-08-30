// Copyright 2022 Indoc Research
// 
// Licensed under the EUPL, Version 1.2 or – as soon they
// will be approved by the European Commission - subsequent
// versions of the EUPL (the "Licence");
// You may not use this work except in compliance with the
// Licence.
// You may obtain a copy of the Licence at:
// 
// https://joinup.ec.europa.eu/collection/eupl/eupl-text-eupl-12
// 
// Unless required by applicable law or agreed to in
// writing, software distributed under the Licence is
// distributed on an "AS IS" basis,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
// express or implied.
// See the Licence for the specific language governing
// permissions and limitations under the Licence.
// 

--
-- PostgreSQL database dump
--

-- Dumped from database version 9.5.23
-- Dumped by pg_dump version 13.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';


--
-- Data for Name: casbin_rule; Type: TABLE DATA; Schema: pilot_casbin; Owner: postgres
--

COPY pilot_casbin.casbin_rule (id, ptype, v0, v1, v2, v3, v4, v5) FROM stdin;
1	p	admin	*	file	view	\N	\N
2	p	admin	*	file	delete	\N	\N
3	p	admin	*	file	upload	\N	\N
4	p	admin	*	file	download	\N	\N
5	p	admin	*	file	copy	\N	\N
6	p	collaborator	*	file	view	\N	\N
7	p	collaborator	*	file	delete	\N	\N
8	p	collaborator	*	file	upload	\N	\N
9	p	collaborator	*	file	download	\N	\N
10	p	contributor	greenroom	file	view	\N	\N
11	p	contributor	greenroom	file	delete	\N	\N
12	p	contributor	greenroom	file	upload	\N	\N
13	p	contributor	greenroom	file	download	\N	\N
14	p	admin	*	announcement	view	\N	\N
15	p	admin	*	announcement	create	\N	\N
16	p	contributor	*	announcement	view	\N	\N
17	p	collaborator	*	announcement	view	\N	\N
18	p	admin	*	file_attribute_template	view	\N	\N
19	p	admin	*	file_attribute_template	create	\N	\N
20	p	admin	*	file_attribute_template	update	\N	\N
21	p	admin	*	file_attribute_template	delete	\N	\N
22	p	admin	*	file_attribute_template	import	\N	\N
23	p	admin	*	file_attribute_template	export	\N	\N
24	p	admin	*	file_attribute_template	attach	\N	\N
25	p	contributor	*	file_attribute_template	view	\N	\N
26	p	collaborator	*	file_attribute_template	create	\N	\N
27	p	collaborator	*	file_attribute_template	update	\N	\N
28	p	collaborator	*	file_attribute_template	delete	\N	\N
29	p	collaborator	*	file_attribute_template	attach	\N	\N
30	p	admin	*	file_attribute	view	\N	\N
31	p	admin	*	file_attribute	create	\N	\N
32	p	admin	*	file_attribute	update	\N	\N
33	p	admin	*	file_attribute	delete	\N	\N
34	p	collaborator	*	file_attribute	view	\N	\N
35	p	collaborator	*	file_attribute	update	\N	\N
36	p	collaborator	*	file_attribute	delete	\N	\N
37	p	admin	*	tags	view	\N	\N
38	p	admin	*	tags	create	\N	\N
39	p	admin	*	tags	update	\N	\N
40	p	admin	*	tags	delete	\N	\N
41	p	contributor	greenroom	tags	view	\N	\N
42	p	contributor	greenroom	tags	create	\N	\N
43	p	contributor	greenroom	tags	update	\N	\N
44	p	contributor	greenroom	tags	delete	\N	\N
45	p	collaborator	*	tags	view	\N	\N
46	p	collaborator	*	tags	create	\N	\N
47	p	collaborator	*	tags	update	\N	\N
48	p	collaborator	*	tags	delete	\N	\N
49	p	admin	*	resource_request	create	\N	\N
50	p	collaborator	*	resource_request	create	\N	\N
51	p	platform_admin	*	resource_request	view	\N	\N
52	p	platform_admin	*	resource_request	update	\N	\N
53	p	platform_admin	*	resource_request	delete	\N	\N
54	p	admin	*	workbench	view	\N	\N
55	p	contributor	*	workbench	view	\N	\N
56	p	collaborator	*	workbench	view	\N	\N
57	p	platform_admin	*	workbench	create	\N	\N
58	p	admin	*	file_stats	view	\N	\N
59	p	contributor	*	file_stats	view	\N	\N
60	p	collaborator	*	file_stats	view	\N	\N
61	p	admin	*	audit_logs	view	\N	\N
62	p	contributor	*	audit_logs	view	\N	\N
63	p	collaborator	*	audit_logs	view	\N	\N
64	p	admin	*	lineage	view	\N	\N
65	p	contributor	greenroom	lineage	view	\N	\N
66	p	admin	*	invite	view	\N	\N
67	p	admin	*	invite	create	\N	\N
68	p	admin	*	project	view	\N	\N
69	p	admin	*	project	update	\N	\N
70	p	contributor	*	project	view	\N	\N
71	p	collaborator	*	project	view	\N	\N
72	p	platform_admin	*	project	create	\N	\N
73	p	admin	*	tasks	view	\N	\N
74	p	admin	*	tasks	delete	\N	\N
75	p	contributor	*	tasks	view	\N	\N
76	p	contributor	*	tasks	delete	\N	\N
77	p	collaborator	*	tasks	view	\N	\N
78	p	collaborator	*	tasks	delete	\N	\N
79	p	admin	*	users	view	\N	\N
85	p	collaborator	*	lineage	view	\N	\N
86	p	contributor	greenroom	file_attribute	view	\N	\N
87	p	contributor	greenroom	file_attribute_template	attach	\N	\N
94	p	collaborator	*	file_attribute_template	view	\N	\N
92	p	contributor	greenroom	file_attribute	update	\N	\N
95	p	admin	*	copyrequest	view	\N	\N
96	p	admin	*	copyrequest	update	\N	\N
97	p	collaborator	*	copyrequest	create	\N	\N
98	p	collaborator	*	copyrequest	view	\N	\N
108	p	platform_admin	*	email	create	\N	\N
117	p	platform_admin	*	notification	view	\N	\N
118	p	platform_admin	*	notification	update	\N	\N
119	p	platform_admin	*	notification	delete	\N	\N
120	p	admin	*	notification	view	\N	\N
121	p	contributor	*	notification	view	\N	\N
122	p	collaborator	*	notification	view	\N	\N
123	p	member	*	notification	view	\N	\N
124	p	visitor	*	notification	view	\N	\N
125	p	platform_admin	*	unsubscribe	create	\N	\N
126	p	admin	*	unsubscribe	create	\N	\N
127	p	contributor	*	unsubscribe	create	\N	\N
128	p	collaborator	*	unsubscribe	create	\N	\N
129	p	member	*	unsubscribe	create	\N	\N
130	p	visitor	*	unsubscribe	create	\N	\N
131	p	platform_admin	*	notification	create	\N	\N
81	p	admin	core	collections	view	\N	\N
82	p	admin	core	collections	create	\N	\N
83	p	admin	core	collections	update	\N	\N
84	p	admin	core	collections	delete	\N	\N
88	p	collaborator	core	collections	view	\N	\N
89	p	collaborator	core	collections	create	\N	\N
90	p	collaborator	core	collections	update	\N	\N
91	p	collaborator	core	collections	delete	\N	\N
93	p	contributor	core	collections	view	\N	\N
\.
--
-- PostgreSQL database dump complete
--

