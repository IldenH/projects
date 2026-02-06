```sql
select
    tracks.TrackId,
    tracks.Name,
    tracks.Composer,
    tracks.Milliseconds,
    tracks.Bytes,
    tracks.UnitPrice,
    albums.Title as Album,
    genres.Name as Genre,
    media_types.Name as MediaType
from tracks
inner join albums using (AlbumId)
inner join genres using (GenreId)
inner join media_types using (MediaTypeId);
```

```sql
select
    albums.Title as Album,
    artists.Name as Artist,
    Count(Distinct tracks.Name) as Tracks
from artists
join albums using (ArtistId)
join tracks using (AlbumId)
group by albums.AlbumId
having Count(*) > 15
order by Tracks desc
;
```

```sql
select
    playlists.Name,
    Count(tracks.TrackId) as Tracks
from playlists
left join playlist_track using (PlaylistId)
left join tracks using (TrackId)
group by playlists.Name
order by Tracks desc
;
```

```sql
select
    l.FirstName || " " || l.LastName as Employee,
    r.FirstName || " " || r.LastName as Manager
from employees as l
left join employees as r
    on l.ReportsTo = r.EmployeeId
;
```
