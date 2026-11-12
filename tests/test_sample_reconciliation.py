import duckdb

from src.data_processing.sample_reconciliation import reconcile


def test_screens_grouping_and_future_mapping_are_separate():
    db = duckdb.connect()
    try:
        db.execute("""
          CREATE TABLE class_returns (
            crsp_fundno VARCHAR, source_return_date DATE, return_month DATE,
            formation_date DATE, net_return DOUBLE
          )
        """)
        db.execute("""
          INSERT INTO class_returns VALUES
            ('000001','2020-01-31','2020-01-31','2020-02-29',0.1),
            ('000002','2020-01-31','2020-01-31','2020-02-29',0.2),
            ('000003','2020-01-31','2020-01-31','2020-02-29',0.1),
            ('000004','2020-01-31','2020-01-31','2020-02-29',2.0),
            ('000005','2020-01-31','2020-01-31','2020-02-29',NULL),
            ('000006','2020-01-31','2020-01-31','2020-02-29',0.1)
        """)
        db.execute("""
          CREATE TABLE summary (
            crsp_fundno VARCHAR, caldt DATE, crsp_obj_cd VARCHAR, fund_name VARCHAR,
            crsp_cl_grp VARCHAR, same_date_rows INTEGER
          )
        """)
        db.execute("""
          INSERT INTO summary VALUES
            ('000001','2019-12-31','EDYG','Growth',NULL,1),
            ('000001','2020-03-31','EDYG','Growth','G1',1),
            ('000002','2019-12-31','EDYG','Growth','G1',1),
            ('000003','2019-12-31',NULL,'Growth','G3',1),
            ('000004','2019-12-31','EDYG','Growth','G4',1),
            ('000005','2019-12-31','EDYG','Growth','G2',1),
            ('000006','2019-12-31','EDYG','Market Index','G6',1)
        """)
        db.execute("""
          CREATE TABLE classes (
            crsp_fundno VARCHAR, return_month DATE, universe_status VARCHAR, summary_date DATE
          )
        """)
        db.execute("""
          INSERT INTO classes VALUES
            ('000001','2020-01-31','missing_class_group','2019-12-31'),
            ('000002','2020-01-31','selected','2019-12-31'),
            ('000003','2020-01-31','selected','2019-12-31'),
            ('000004','2020-01-31','selected','2019-12-31'),
            ('000005','2020-01-31','selected','2019-12-31'),
            ('000006','2020-01-31','index_fund','2019-12-31')
        """)
        result = reconcile(db, '2020-01-01', '2020-01-31', '2020-02-29', '2020-02-29')
        w, m = result['waterfall'], result['mapping']
        assert [w[k] for k in ('source_rows','in_window','objective_known','active_objective',
                              'passed_name','passed_return')] == [6,6,5,5,4,3]
        assert w['selected_missing_return'] == 1
        assert (m['latest_missing'],m['strict_mapped'],m['latest_singleton']) == (1,2,3)
        assert (m['last_nonblank_missing'],m['last_nonblank_singleton']) == (1,3)
        assert (m['full_file_missing'],m['full_file_singleton']) == (0,2)
        assert (m['future_only_class_months'],m['future_only_classes']) == (1,1)
        assert (m['first_group_after_formation'], m['first_group_unavailable_at_lag']) == (1,1)
        assert result['retrospective_only_local_first_reason'] == {'missing_class_group':1}
        assert result['lagged_only_retrospective_first_reason'] == {
            'extreme_return':1,'unknown_objective':1
        }
        assert result['annual_alignment'] == [
            {'year':2020,'total':6,'both':2,'retro_only':1,'lagged_only':2,'neither':1}
        ]
    finally:
        db.close()


def test_last_nonblank_asof_can_fill_a_later_blank_without_future_data():
    db = duckdb.connect()
    try:
        db.execute("""
          CREATE TABLE class_returns AS SELECT * FROM (VALUES
            ('000001',DATE '2020-01-31',DATE '2020-01-31',DATE '2020-02-29',0.1),
            ('000002',DATE '2020-01-31',DATE '2020-01-31',DATE '2020-02-29',0.1)
          ) AS x(crsp_fundno,source_return_date,return_month,formation_date,net_return)
        """)
        db.execute("""
          CREATE TABLE summary AS SELECT * FROM (VALUES
            ('000001',DATE '2019-09-30','EDYG','Growth','G1',1),
            ('000001',DATE '2019-12-31','EDYG','Growth',NULL,1),
            ('000002',DATE '2019-12-31','EDYG','Growth','G1',1)
          ) AS x(crsp_fundno,caldt,crsp_obj_cd,fund_name,crsp_cl_grp,same_date_rows)
        """)
        db.execute("""
          CREATE TABLE classes AS SELECT * FROM (VALUES
            ('000001',DATE '2020-01-31','missing_class_group',DATE '2019-12-31'),
            ('000002',DATE '2020-01-31','selected',DATE '2019-12-31')
          ) AS x(crsp_fundno,return_month,universe_status,summary_date)
        """)
        result = reconcile(db, '2020-01-01', '2020-01-31', '2020-02-29', '2020-02-29')
        m = result['mapping']
        assert (m['latest_missing'], m['latest_singleton']) == (1, 2)
        assert (m['last_nonblank_missing'], m['last_nonblank_singleton']) == (0, 1)
        assert m['future_only_class_months'] == 0
    finally:
        db.close()


def test_group_seen_before_formation_can_still_miss_the_availability_cutoff():
    db = duckdb.connect()
    try:
        db.execute("""
          CREATE TABLE class_returns AS SELECT * FROM (VALUES
            ('000001',DATE '2020-01-31',DATE '2020-01-31',DATE '2020-02-29',0.1)
          ) AS x(crsp_fundno,source_return_date,return_month,formation_date,net_return)
        """)
        db.execute("""
          CREATE TABLE summary AS SELECT * FROM (VALUES
            ('000001',DATE '2019-12-31','EDYG','Growth',NULL,1),
            ('000001',DATE '2020-02-15','EDYG','Growth','G1',1)
          ) AS x(crsp_fundno,caldt,crsp_obj_cd,fund_name,crsp_cl_grp,same_date_rows)
        """)
        db.execute("""
          CREATE TABLE classes AS SELECT * FROM (VALUES
            ('000001',DATE '2020-01-31','missing_class_group',DATE '2019-12-31')
          ) AS x(crsp_fundno,return_month,universe_status,summary_date)
        """)
        m = reconcile(db, '2020-01-01', '2020-01-31', '2020-02-29', '2020-02-29')['mapping']
        assert m['future_only_class_months'] == 1
        assert m['first_group_after_formation'] == 0
        assert m['first_group_unavailable_at_lag'] == 1
    finally:
        db.close()
