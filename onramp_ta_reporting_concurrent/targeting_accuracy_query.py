# targeting_accuracy_query module
# Module holds the class => TargetingAccuracyQuery - manages Hive query template
# Class responsible to populate the query with Jira ticket sourced variables
#


class TargetingAccuracyQuery(object):

    @staticmethod
    def weekly_query(pixel, profile_ids, report_start_date, report_end_date):
        query = """
        set hive.execution.engine = tez;
        set fs.s3n.block.size=128000000;
        set fs.s3a.block.size=128000000;
        set hive.exec.reducers.max = 60;

        select 
        x.TOTAL_IMPRESSIONS, 
        y.ELIGIBLE_INDIVIDUALS,
        nvl((round((y.ELIGIBLE_INDIVIDUALS / x.TOTAL_IMPRESSIONS), 4) * 100), 0) as IND_MATCH_PERCENT,
        z.MATCHED_INDIVIDUALS, 
        nvl((round((z.MATCHED_INDIVIDUALS / x.TOTAL_IMPRESSIONS), 4) * 100), 0) as TARGETING_ACCURACY
        from
        (select 1 as link, count(*) as TOTAL_IMPRESSIONS from core_digital.unified_impression
        where data_source_id_part = 6
        and source = 'save'
        and pixel_id in ({pixel})
        and data_date between {start_date} and {end_date}
        ) x
        left join
        (
        select 1 as link, count(b.individual_id) AS ELIGIBLE_INDIVIDUALS
        from
        (select na_guid_id from core_digital.unified_impression
        where data_source_id_part = 6
        and source = 'save'
        and pixel_id in ({pixel})
        and data_date between {start_date} and {end_date}
        ) a
        inner join core_digital.best_matched_cookies_history_ind b
        on a.na_guid_id = b.guid
        ) y on x.link = y.link
        left join
        (
        select 1 as link, count(c.individual_id) AS MATCHED_INDIVIDUALS
        from
        (select na_guid_id from core_digital.unified_impression
        where data_source_id_part = 6
        and source = 'save'
        and pixel_id in ({pixel})
        and data_date between {start_date} and {end_date}
        ) a
        inner join core_digital.best_matched_cookies_history_ind b
        on a.na_guid_id = b.guid
        inner join
        (select individual_id from core_shared.individual_segment_values_vw
        where segment_id in ({profile_ids})
        ) c
        on c.individual_id = b.individual_id
        ) z on x.link = z.link
        """.format(start_date=report_start_date, end_date=report_end_date,
                   pixel=",".join(pixel), profile_ids=",".join(profile_ids))
        return query
